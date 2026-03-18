import subprocess
import unittest
from unittest.mock import patch

from flowdl.integrations.whispercpp_wrapper import transcribe_with_whispercpp
from flowdl.utils.errors import DependencyMissingError


class WhisperCppWrapperTests(unittest.TestCase):
    def test_transcribe_with_whispercpp_builds_command(self) -> None:
        with patch("flowdl.integrations.whispercpp_wrapper.subprocess.run") as run_mock:
            txt_path, json_path = transcribe_with_whispercpp(
                input_audio="/tmp/in.wav",
                model_path="/models/ggml-base.en.bin",
                output_prefix="/tmp/out",
                language="en",
            )

        self.assertEqual(txt_path, "/tmp/out.txt")
        self.assertEqual(json_path, "/tmp/out.json")
        run_mock.assert_called_once_with(
            [
                "whisper-cli",
                "-m",
                "/models/ggml-base.en.bin",
                "-f",
                "/tmp/in.wav",
                "-of",
                "/tmp/out",
                "-otxt",
                "-oj",
                "-l",
                "en",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

    def test_transcribe_with_whispercpp_missing_binary(self) -> None:
        with patch(
            "flowdl.integrations.whispercpp_wrapper.subprocess.run",
            side_effect=FileNotFoundError(),
        ):
            with self.assertRaises(DependencyMissingError):
                transcribe_with_whispercpp(
                    input_audio="/tmp/in.wav",
                    model_path="/models/model.bin",
                    output_prefix="/tmp/out",
                )

    def test_transcribe_with_whispercpp_process_failure(self) -> None:
        error = subprocess.CalledProcessError(1, ["whisper-cli"], stderr="model error")
        with patch("flowdl.integrations.whispercpp_wrapper.subprocess.run", side_effect=error):
            with self.assertRaises(RuntimeError) as ctx:
                transcribe_with_whispercpp(
                    input_audio="/tmp/in.wav",
                    model_path="/models/model.bin",
                    output_prefix="/tmp/out",
                )
        self.assertIn("whisper.cpp failed", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

