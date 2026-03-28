"""Tests for local STT (Whisper) model download functionality."""

import unittest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from pathlib import Path
import tempfile
import shutil


class TestLocalSTTDownload(unittest.TestCase):
    """Test Whisper STT model download functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp(prefix="test_samantha_stt_"))

    def tearDown(self):
        """Clean up test fixtures."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_stt_initialization(self):
        """Test LocalSTT can be initialized without errors."""
        # Note: We can't fully test this without numpy, but we can test the structure
        try:
            from samantha.stt_local import LocalSTT

            stt = LocalSTT(model_size="base", device="cpu")

            self.assertEqual(stt.model_size, "base")
            self.assertEqual(stt.device, "cpu")
            self.assertEqual(stt.language, "en")
            self.assertIsNone(stt._model)  # Model should be lazy-loaded
        except ImportError as e:
            # numpy not available in test environment
            self.skipTest(f"Cannot test without dependencies: {e}")

    def test_model_size_helper(self):
        """Test _get_model_size_mb returns correct sizes."""
        try:
            from samantha.stt_local import LocalSTT

            test_cases = [
                ("tiny", "75"),
                ("base", "145"),
                ("small", "488"),
                ("medium", "1.5GB"),
                ("large-v3", "3GB"),
                ("unknown-model", "unknown"),
            ]

            for model_name, expected_size in test_cases:
                stt = LocalSTT(model_size=model_name, device="cpu")
                result = stt._get_model_size_mb()
                self.assertEqual(result, expected_size)
        except ImportError as e:
            self.skipTest(f"Cannot test without dependencies: {e}")

    def test_device_auto_detection_no_cuda(self):
        """Test device auto-detection falls back to CPU when CUDA unavailable."""
        try:
            from samantha.stt_local import LocalSTT

            with patch('samantha.stt_local.torch', side_effect=ImportError):
                stt = LocalSTT(model_size="base", device="auto")
                self.assertEqual(stt.device, "cpu")
        except ImportError as e:
            self.skipTest(f"Cannot test without dependencies: {e}")

    @patch('samantha.stt_local.torch')
    def test_device_auto_detection_with_cuda(self, mock_torch):
        """Test device auto-detection uses CUDA when available."""
        try:
            from samantha.stt_local import LocalSTT

            mock_torch.cuda.is_available.return_value = True

            stt = LocalSTT(model_size="base", device="auto")
            self.assertEqual(stt.device, "cuda")
        except ImportError as e:
            self.skipTest(f"Cannot test without dependencies: {e}")

    def test_compute_type_auto_selection(self):
        """Test compute type is automatically selected based on device."""
        try:
            from samantha.stt_local import LocalSTT

            # CPU should use int8
            stt_cpu = LocalSTT(model_size="base", device="cpu", compute_type=None)
            self.assertEqual(stt_cpu.compute_type, "int8")

            # CUDA should use float16
            stt_cuda = LocalSTT(model_size="base", device="cuda", compute_type=None)
            self.assertEqual(stt_cuda.compute_type, "float16")
        except ImportError as e:
            self.skipTest(f"Cannot test without dependencies: {e}")

    @patch('samantha.stt_local.WhisperModel')
    @patch('samantha.stt_local.Path')
    def test_model_download_progress_messages(self, mock_path_class, mock_whisper):
        """Test that model loading shows progress messages on first download."""
        try:
            from samantha.stt_local import LocalSTT

            # Mock cache directory to simulate first download
            mock_cache = MagicMock()
            mock_cache.exists.return_value = True
            mock_cache.glob.return_value = []  # No cached model

            mock_path = MagicMock()
            mock_path.home.return_value = mock_path
            mock_path.__truediv__ = lambda self, other: mock_cache
            mock_path_class.home.return_value = mock_path

            stt = LocalSTT(model_size="base", device="cpu")

            with patch('builtins.print') as mock_print:
                # Access the model property to trigger download
                _ = stt.model

            # Check that progress messages were printed
            print_calls = [str(call) for call in mock_print.call_args_list]
            has_download_msg = any("Downloading" in call for call in print_calls)
            has_ready_msg = any("ready" in call.lower() for call in print_calls)

            self.assertTrue(has_download_msg, "Should print downloading message")
            self.assertTrue(has_ready_msg, "Should print ready message")
        except ImportError as e:
            self.skipTest(f"Cannot test without dependencies: {e}")

    @patch('samantha.stt_local.WhisperModel')
    @patch('samantha.stt_local.Path')
    def test_model_no_messages_when_cached(self, mock_path_class, mock_whisper):
        """Test that model loading is silent when model already cached."""
        try:
            from samantha.stt_local import LocalSTT

            # Mock cache directory to simulate cached model
            mock_cache = MagicMock()
            mock_cache.exists.return_value = True
            mock_cache.glob.return_value = [MagicMock()]  # Model exists

            mock_path = MagicMock()
            mock_path.home.return_value = mock_path
            mock_path.__truediv__ = lambda self, other: mock_cache
            mock_path_class.home.return_value = mock_path

            stt = LocalSTT(model_size="base", device="cpu")

            with patch('builtins.print') as mock_print:
                # Access the model property
                _ = stt.model

            # Check that NO progress messages were printed
            print_calls = [str(call) for call in mock_print.call_args_list]
            has_download_msg = any("Downloading" in call for call in print_calls)

            self.assertFalse(has_download_msg, "Should not print downloading message for cached model")
        except ImportError as e:
            self.skipTest(f"Cannot test without dependencies: {e}")

    @patch('samantha.stt_local.WhisperModel')
    def test_model_loading_error_message(self, mock_whisper):
        """Test that model loading failure provides helpful error message."""
        try:
            from samantha.stt_local import LocalSTT

            # Mock WhisperModel to raise an exception
            mock_whisper.side_effect = Exception("Network error")

            stt = LocalSTT(model_size="base", device="cpu")

            with self.assertRaises(RuntimeError) as context:
                _ = stt.model

            error_msg = str(context.exception)
            self.assertIn("Failed to load Whisper model", error_msg)
            self.assertIn("base", error_msg)
            self.assertIn("internet", error_msg.lower())
            self.assertIn("disk space", error_msg.lower())
            self.assertIn("pip install", error_msg.lower())
        except ImportError as e:
            self.skipTest(f"Cannot test without dependencies: {e}")

    def test_lazy_loading_behavior(self):
        """Test that model is not loaded until accessed."""
        try:
            from samantha.stt_local import LocalSTT

            with patch('samantha.stt_local.WhisperModel') as mock_whisper:
                stt = LocalSTT(model_size="base", device="cpu")

                # Model should not be loaded yet
                mock_whisper.assert_not_called()
                self.assertIsNone(stt._model)

                # Now access it
                with patch('samantha.stt_local.Path'):
                    _ = stt.model

                # Now it should be loaded
                mock_whisper.assert_called_once()
        except ImportError as e:
            self.skipTest(f"Cannot test without dependencies: {e}")


class TestSTTIntegration(unittest.TestCase):
    """Integration tests for STT functionality."""

    def test_stt_import(self):
        """Test that LocalSTT module can be imported."""
        try:
            from samantha.stt_local import LocalSTT
            self.assertTrue(callable(LocalSTT))
        except ImportError as e:
            self.skipTest(f"Cannot test without dependencies: {e}")

    def test_stt_has_required_methods(self):
        """Test that LocalSTT has all required methods."""
        try:
            from samantha.stt_local import LocalSTT

            stt = LocalSTT(model_size="base", device="cpu")

            # Check that required methods exist
            self.assertTrue(hasattr(stt, 'transcribe_file'))
            self.assertTrue(hasattr(stt, 'transcribe_audio_data'))
            self.assertTrue(hasattr(stt, 'listen'))
            self.assertTrue(hasattr(stt, 'cleanup'))
            self.assertTrue(hasattr(stt, 'model'))
        except ImportError as e:
            self.skipTest(f"Cannot test without dependencies: {e}")


if __name__ == '__main__':
    unittest.main()
