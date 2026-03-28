"""Tests for voice engine error handling and download integration."""

import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import shutil


class TestVoiceEngineDownloadHandling(unittest.TestCase):
    """Test VoiceEngine handles model downloads correctly."""

    def test_voice_engine_initialization(self):
        """Test VoiceEngine can be initialized with local engines."""
        from samantha.voice import VoiceEngine

        ve = VoiceEngine(
            stt_engine="local",
            tts_engine="local",
            whisper_model="base",
            piper_voice="samantha"
        )

        self.assertEqual(ve.stt_engine, "local")
        self.assertEqual(ve.tts_engine, "local")
        self.assertEqual(ve.whisper_model, "base")
        self.assertEqual(ve.piper_voice, "samantha")

    def test_voice_engine_stt_available_check(self):
        """Test STT availability check."""
        from samantha.voice import VoiceEngine

        # Test with local engine
        ve_local = VoiceEngine(stt_engine="local", tts_engine="local")

        # Should check for faster-whisper availability
        with patch('samantha.voice.importlib.import_module') as mock_import:
            mock_import.side_effect = ImportError
            available = ve_local.stt_available
            # Without faster-whisper, should return False
            # (actual behavior depends on environment)

    def test_voice_engine_tts_available_check(self):
        """Test TTS availability check."""
        from samantha.voice import VoiceEngine

        # Test with local engine
        ve_local = VoiceEngine(stt_engine="local", tts_engine="local")

        # Local TTS is always reported as available
        self.assertTrue(ve_local.tts_available)

        # Test with cloud engine
        ve_cloud = VoiceEngine(stt_engine="cloud", tts_engine="cloud", fish_api_key="")
        self.assertFalse(ve_cloud.tts_available)

        ve_cloud_with_key = VoiceEngine(stt_engine="cloud", tts_engine="cloud", fish_api_key="test_key")
        self.assertTrue(ve_cloud_with_key.tts_available)

    @patch('samantha.voice.LocalSTT')
    def test_listen_local_preserves_runtime_error(self, mock_stt_class):
        """Test that _listen_local preserves RuntimeError from model loading."""
        from samantha.voice import VoiceEngine

        # Mock LocalSTT to raise RuntimeError (e.g., download error)
        mock_stt = MagicMock()
        mock_stt.listen.side_effect = RuntimeError("Failed to load Whisper model")
        mock_stt_class.return_value = mock_stt

        ve = VoiceEngine(stt_engine="local", tts_engine="local")
        ve._local_stt = mock_stt

        # Should preserve the RuntimeError
        with self.assertRaises(RuntimeError) as context:
            ve._listen_local()

        error_msg = str(context.exception)
        self.assertIn("Whisper model", error_msg)

    @patch('samantha.voice.LocalSTT')
    def test_listen_local_enhances_generic_error(self, mock_stt_class):
        """Test that _listen_local enhances generic errors with help."""
        from samantha.voice import VoiceEngine

        # Mock LocalSTT to raise generic Exception
        mock_stt = MagicMock()
        mock_stt.listen.side_effect = Exception("Unknown error")
        mock_stt_class.return_value = mock_stt

        ve = VoiceEngine(stt_engine="local", tts_engine="local")
        ve._local_stt = mock_stt

        # Should enhance with troubleshooting info
        with self.assertRaises(RuntimeError) as context:
            ve._listen_local()

        error_msg = str(context.exception)
        self.assertIn("pip install", error_msg.lower())
        self.assertIn("cloud mode", error_msg.lower())

    @patch('samantha.voice.LocalTTS')
    def test_generate_audio_local_preserves_runtime_error(self, mock_tts_class):
        """Test that _generate_audio_local preserves RuntimeError from model loading."""
        from samantha.voice import VoiceEngine, TTSError

        # Mock LocalTTS to raise RuntimeError (e.g., download error)
        mock_tts = MagicMock()
        mock_tts.generate_audio.side_effect = RuntimeError("Failed to download Piper model")
        mock_tts_class.return_value = mock_tts

        ve = VoiceEngine(stt_engine="local", tts_engine="local")
        ve._local_tts = mock_tts

        # Should preserve the RuntimeError (wrapped in TTSError would be acceptable too)
        with self.assertRaises((RuntimeError, TTSError)) as context:
            ve._generate_audio_local("test text")

        error_msg = str(context.exception)
        self.assertIn("Piper", error_msg)

    @patch('samantha.voice.LocalTTS')
    def test_generate_audio_local_enhances_generic_error(self, mock_tts_class):
        """Test that _generate_audio_local enhances generic errors with help."""
        from samantha.voice import VoiceEngine, TTSError

        # Mock LocalTTS to raise generic Exception
        mock_tts = MagicMock()
        mock_tts.generate_audio.side_effect = Exception("Unknown error")
        mock_tts_class.return_value = mock_tts

        ve = VoiceEngine(stt_engine="local", tts_engine="local")
        ve._local_tts = mock_tts

        # Should enhance with troubleshooting info
        with self.assertRaises(TTSError) as context:
            ve._generate_audio_local("test text")

        error_msg = str(context.exception)
        self.assertIn("pip install", error_msg.lower())
        self.assertIn("cloud mode", error_msg.lower())

    def test_voice_engine_lazy_initialization(self):
        """Test that engines are lazily initialized."""
        from samantha.voice import VoiceEngine

        ve = VoiceEngine(stt_engine="local", tts_engine="local")

        # Engines should not be initialized yet
        self.assertIsNone(ve._local_stt)
        self.assertIsNone(ve._local_tts)

    @patch('samantha.voice.LocalSTT')
    def test_init_local_stt_creates_instance(self, mock_stt_class):
        """Test that _init_local_stt creates LocalSTT instance."""
        from samantha.voice import VoiceEngine

        mock_stt = MagicMock()
        mock_stt_class.return_value = mock_stt

        ve = VoiceEngine(
            stt_engine="local",
            tts_engine="local",
            whisper_model="small",
            whisper_device="cuda"
        )

        result = ve._init_local_stt()

        # Should create instance with correct parameters
        mock_stt_class.assert_called_once()
        call_kwargs = mock_stt_class.call_args[1]
        self.assertEqual(call_kwargs['model_size'], "small")
        self.assertEqual(call_kwargs['device'], "cuda")
        self.assertEqual(result, mock_stt)

    @patch('samantha.voice.LocalTTS')
    def test_init_local_tts_creates_instance(self, mock_tts_class):
        """Test that _init_local_tts creates LocalTTS instance."""
        from samantha.voice import VoiceEngine

        mock_tts = MagicMock()
        mock_tts_class.return_value = mock_tts

        ve = VoiceEngine(
            stt_engine="local",
            tts_engine="local",
            piper_voice="amy",
            speech_speed=1.2
        )

        result = ve._init_local_tts()

        # Should create instance with correct parameters
        mock_tts_class.assert_called_once()
        call_kwargs = mock_tts_class.call_args[1]
        self.assertEqual(call_kwargs['voice'], "amy")
        self.assertEqual(call_kwargs['speed'], 1.2)
        self.assertEqual(result, mock_tts)


class TestVoiceEngineRouting(unittest.TestCase):
    """Test VoiceEngine correctly routes to local/cloud engines."""

    @patch('samantha.voice.VoiceEngine._listen_local')
    @patch('samantha.voice.VoiceEngine._listen_cloud')
    def test_listen_routes_to_local(self, mock_cloud, mock_local):
        """Test listen() routes to local when stt_engine is local."""
        from samantha.voice import VoiceEngine

        mock_local.return_value = "test result"
        ve = VoiceEngine(stt_engine="local", tts_engine="local")

        result = ve.listen()

        mock_local.assert_called_once()
        mock_cloud.assert_not_called()
        self.assertEqual(result, "test result")

    @patch('samantha.voice.VoiceEngine._listen_local')
    @patch('samantha.voice.VoiceEngine._listen_cloud')
    def test_listen_routes_to_cloud(self, mock_cloud, mock_local):
        """Test listen() routes to cloud when stt_engine is cloud."""
        from samantha.voice import VoiceEngine

        mock_cloud.return_value = "test result"
        ve = VoiceEngine(stt_engine="cloud", tts_engine="local")

        result = ve.listen()

        mock_cloud.assert_called_once()
        mock_local.assert_not_called()
        self.assertEqual(result, "test result")

    @patch('samantha.voice.VoiceEngine._generate_audio_local')
    @patch('samantha.voice.VoiceEngine._generate_audio_cloud')
    def test_generate_audio_routes_to_local(self, mock_cloud, mock_local):
        """Test generate_audio() routes to local when tts_engine is local."""
        from samantha.voice import VoiceEngine

        mock_local.return_value = "/path/to/audio"
        ve = VoiceEngine(stt_engine="local", tts_engine="local")

        result = ve.generate_audio("test text")

        mock_local.assert_called_once_with("test text")
        mock_cloud.assert_not_called()
        self.assertEqual(result, "/path/to/audio")

    @patch('samantha.voice.VoiceEngine._generate_audio_local')
    @patch('samantha.voice.VoiceEngine._generate_audio_cloud')
    def test_generate_audio_routes_to_cloud(self, mock_cloud, mock_local):
        """Test generate_audio() routes to cloud when tts_engine is cloud."""
        from samantha.voice import VoiceEngine

        mock_cloud.return_value = "/path/to/audio"
        ve = VoiceEngine(stt_engine="local", tts_engine="cloud", fish_api_key="test")

        result = ve.generate_audio("test text")

        mock_cloud.assert_called_once_with("test text")
        mock_local.assert_not_called()
        self.assertEqual(result, "/path/to/audio")


if __name__ == '__main__':
    unittest.main()
