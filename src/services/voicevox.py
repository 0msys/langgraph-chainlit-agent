import requests
import base64
import json
import re
import os

from openai import OpenAI


class SpeakerData:
    """
    SpeakerDataクラス
    VOICEVOXのspeaker情報を取得するためのクラス
    """

    def __init__(self, domain: str = None):
        self.domain = domain or os.getenv(
            "VOICEVOX_API_DOMAIN", "http://voicevox_engine:50021/"
        )
        self.data = self._load_data()

    def _load_data(self) -> dict:
        """speakerの一覧をAPIから取得し、辞書形式で返す"""
        speakers_json = requests.get(url=f"{self.domain}speakers").json()
        return {
            item["name"]: {style["name"]: style["id"] for style in item["styles"]}
            for item in speakers_json
        }

    def get_all_speaker_and_style_list(self) -> list:
        """speakerとstyleの組み合わせに対するspeaker_idのリストを取得"""
        return [
            {
                f"{speaker}-{style}": self.data[speaker][style]
                for style in self.data[speaker]
            }
            for speaker in self.data
        ]

    def get_all_speaker_and_style_dict(self) -> dict:
        """speakerとstyleの組み合わせに対するspeaker_idの辞書を取得"""
        return {
            f"{speaker} - {style}": str(self.data[speaker][style])
            for speaker in self.data
            for style in self.data[speaker]
        }


class Voicevox:
    """
    Voicevoxクラス
    VOICEVOX APIを利用するためのクラス
    """

    def __init__(
        self,
        speaker_name: str = None,
        style_name: str = None,
        speaker_id: str = None,
        file_path: str = "./",
    ):
        self.domain = os.getenv("VOICEVOX_API_DOMAIN", "http://voicevox_engine:50021/")
        self.speaker_id = self._get_speaker_id(speaker_name, style_name, speaker_id)
        self.file_path = file_path

    def _get_speaker_id(
        self, speaker_name: str, style_name: str, speaker_id: str
    ) -> str:
        """speaker_idを取得するためのヘルパーメソッド"""
        if speaker_id:
            return speaker_id
        elif speaker_name and style_name:
            speakers = SpeakerData().data
            return speakers[speaker_name][style_name]
        else:
            raise ValueError(
                "speaker_id or speaker_name and style_name must be provided"
            )

    def _post_audio_query(self, text: str) -> json:
        """音声クエリをPOSTし、結果を返す"""
        response = requests.post(
            url=f"{self.domain}audio_query",
            params={"text": text, "speaker": self.speaker_id},
        )
        return response.json()

    def _post_synthesis(self, text: str) -> bytes:
        """音声合成を行い、結果のバイナリデータを返す"""
        query = self._post_audio_query(text)
        response = requests.post(
            url=f"{self.domain}synthesis",
            params={"speaker": self.speaker_id},
            json=query,
        )
        return response.content

    def post_synthesis_returned_in_base64(
        self, text: str, use_manuscript: bool = False
    ) -> str:
        """テキストを入力し、音声ファイルを生成してbase64形式で返す"""
        if use_manuscript:
            text = self._create_manuscript(text)
        audio_data = self._post_synthesis(text)
        return base64.b64encode(audio_data).decode()

    def post_synthesis_returned_in_file(
        self, text: str, use_manuscript: bool = False, file_name: str = "output"
    ) -> str:
        """テキストを入力し、音声ファイルを生成してファイルパスを返す"""
        if use_manuscript:
            text = self._create_manuscript(text)
        audio_data = self._post_synthesis(text)
        file_path = os.path.join(self.file_path, f"{file_name}.wav")
        with open(file_path, "wb") as file:
            file.write(audio_data)
        return file_path

    def _create_manuscript(self, text: str) -> str:
        """テキストを入力し、読み上げ原稿を生成して返す"""
        client = OpenAI()
        system_prompt = re.sub(
            r"\n\s*",
            "\n",
            """あなたは読み上げテキスト生成器です。ユーザーから提供された文章を、読み上げ原稿を返答してください。その際以下のルールに従ってください。
                    - アルファベットの固有名詞はカタカナにし、漢字はひらがなにするなど、読み間違いをしないようにする
                    - URLやコードブロックについては、そのまま読み上げるのではなく、画面を確認するように促すなど言い換えを行う
                    入力文章：""",
        )
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{text}\n\n読み上げ原稿\n："},
            ],
        )
        return completion.choices[0].message.content


if __name__ == "__main__":
    voicevox = Voicevox(speaker_name="ずんだもん", style_name="ノーマル")
    text = "こんにちは"
    audio_file = voicevox.post_synthesis_returned_in_file(text, use_manuscript=True)
    print(audio_file)
