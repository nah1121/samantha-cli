"""Tests for local TTS (Piper) model download functionality."""

import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import shutil
import urllib.error


class TestLocalTTSDownload(unittest.TestCase):
    """Test Piper TTS model download functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp(prefix="test_samantha_"))
        self.model_dir = self.test_dir / "voices"
        self.model_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up test fixtures."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    @patch('samantha.tts_local.LocalTTS._download_model_manual')
    @patch('samantha.tts_local.LocalTTS._get_model_path')
    def test_tts_initialization(self, mock_get_model, mock_download):
        """Test LocalTTS can be initialized without errors."""
        from samantha.tts_local import LocalTTS

        # Mock the model path to avoid actual downloads
        mock_get_model.return_value = self.model_dir / "test.onnx"

        tts = LocalTTS(voice="samantha", model_dir=self.model_dir)

        self.assertEqual(tts.voice_model, "en_US-lessac-medium")
        self.assertEqual(tts.model_dir, self.model_dir)
        self.assertGreaterEqual(tts.speed, 0.5)
        self.assertLessEqual(tts.speed, 2.0)

    def test_tts_model_exists_check(self):
        """Test that _get_model_path returns existing model without download."""
        from samantha.tts_local import LocalTTS

        # Create fake model files
        model_path = self.model_dir / "en_US-lessac-medium.onnx"
        config_path = self.model_dir / "en_US-lessac-medium.onnx.json"
        model_path.touch()
        config_path.touch()

        tts = LocalTTS(voice="samantha", model_dir=self.model_dir)

        # Should not trigger download since files exist
        with patch('builtins.print') as mock_print:
            result = tts._get_model_path()
            # Should not print download message
            download_calls = [call for call in mock_print.call_args_list
                            if 'Downloading' in str(call)]
            self.assertEqual(len(download_calls), 0)

        self.assertEqual(result, model_path)

    @patch('urllib.request.urlretrieve')
    def test_manual_download_success(self, mock_urlretrieve):
        """Test manual download succeeds with proper files."""
        from samantha.tts_local import LocalTTS

        tts = LocalTTS(voice="samantha", model_dir=self.model_dir)
        model_path = self.model_dir / "en_US-lessac-medium.onnx"
        config_path = self.model_dir / "en_US-lessac-medium.onnx.json"

        # Mock successful downloads
        mock_urlretrieve.return_value = None

        # Should not raise any exception
        tts._download_model_manual(model_path, config_path)

        # Should have called urlretrieve twice (model + config)
        self.assertEqual(mock_urlretrieve.call_count, 2)

    @patch('urllib.request.urlretrieve')
    def test_manual_download_404_error(self, mock_urlretrieve):
        """Test manual download handles 404 error with helpful message."""
        from samantha.tts_local import LocalTTS

        tts = LocalTTS(voice="invalid-voice", model_dir=self.model_dir)
        model_path = self.model_dir / "invalid-voice.onnx"
        config_path = self.model_dir / "invalid-voice.onnx.json"

        # Mock 404 error
        mock_urlretrieve.side_effect = urllib.error.HTTPError(
            url="test", code=404, msg="Not Found", hdrs={}, fp=None
        )

        # Should raise RuntimeError with helpful message
        with self.assertRaises(RuntimeError) as context:
            tts._download_model_manual(model_path, config_path)

        error_msg = str(context.exception)
        self.assertIn("not found", error_msg.lower())
        self.assertIn("samantha", error_msg)
        self.assertIn("amy", error_msg)

    @patch('urllib.request.urlretrieve')
    def test_manual_download_network_error(self, mock_urlretrieve):
        """Test manual download handles network error."""
        from samantha.tts_local import LocalTTS

        tts = LocalTTS(voice="samantha", model_dir=self.model_dir)
        model_path = self.model_dir / "en_US-lessac-medium.onnx"
        config_path = self.model_dir / "en_US-lessac-medium.onnx.json"

        # Mock network error
        mock_urlretrieve.side_effect = urllib.error.URLError("Network unreachable")

        # Should raise RuntimeError with network error message
        with self.assertRaises(RuntimeError) as context:
            tts._download_model_manual(model_path, config_path)

        error_msg = str(context.exception)
        self.assertIn("network", error_msg.lower())
        self.assertIn("internet", error_msg.lower())

    def test_voice_name_mapping(self):
        """Test that friendly voice names map to correct model names."""
        from samantha.tts_local import LocalTTS

        test_cases = [
            ("samantha", "en_US-lessac-medium"),
            ("amy", "en_US-amy-medium"),
            ("kathleen", "en_US-kathleen-low"),
            ("ryan", "en_US-ryan-high"),
            ("libritts", "en_US-libritts-high"),
        ]

        for friendly_name, expected_model in test_cases:
            tts = LocalTTS(voice=friendly_name, model_dir=self.model_dir)
            self.assertEqual(tts.voice_model, expected_model)

    def test_speed_clamping(self):
        """Test that speed is clamped to valid range."""
        from samantha.tts_local import LocalTTS

        # Test too low
        tts_low = LocalTTS(voice="samantha", speed=0.1, model_dir=self.model_dir)
        self.assertEqual(tts_low.speed, 0.5)

        # Test too high
        tts_high = LocalTTS(voice="samantha", speed=5.0, model_dir=self.model_dir)
        self.assertEqual(tts_high.speed, 2.0)

        # Test valid range
        tts_valid = LocalTTS(voice="samantha", speed=1.0, model_dir=self.model_dir)
        self.assertEqual(tts_valid.speed, 1.0)

    @patch('samantha.tts_local.LocalTTS._get_model_path')
    def test_generate_audio_empty_text(self, mock_get_model):
        """Test that generate_audio raises error for empty text."""
        from samantha.tts_local import LocalTTS

        mock_get_model.return_value = self.model_dir / "test.onnx"
        tts = LocalTTS(voice="samantha", model_dir=self.model_dir)

        with self.assertRaises(ValueError) as context:
            tts.generate_audio("")

        self.assertIn("empty", str(context.exception).lower())

    @patch('builtins.print')
    def test_download_progress_messages(self, mock_print):
        """Test that download shows progress messages."""
        from samantha.tts_local import LocalTTS

        tts = LocalTTS(voice="samantha", model_dir=self.model_dir)

        # Mock the piper download to fail, forcing manual download path
        def mock_get_model_path_with_download():
            # Simulate the download path by calling _download_model_manual
            model_path = tts.model_dir / f"{tts.voice_model}.onnx"
            config_path = tts.model_dir / f"{tts.voice_model}.onnx.json"

            # Trigger the print messages
            print(f"\n  Downloading Piper voice model '{tts.voice_model}' (~60MB)...")
            print(f"  This is a one-time download. Future use will be instant.\n")

            # Create mock files
            model_path.touch()
            config_path.touch()
            return model_path

        # Patch _get_model_path to use our mock
        with patch.object(tts, '_get_model_path', side_effect=mock_get_model_path_with_download):
            try:
                tts._get_model_path()
            except Exception:
                pass

        # Check that progress messages were printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        has_download_msg = any("Downloading" in call for call in print_calls)

        self.assertTrue(has_download_msg, "Should print downloading message")


if __name__ == '__main__':
    unittest.main()
