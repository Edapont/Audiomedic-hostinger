import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { API } from '../App';
import axios from 'axios';
import { Mic, Square, Upload, ArrowLeft, Loader } from 'lucide-react';

function Recorder() {
  const navigate = useNavigate();
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioBlob, setAudioBlob] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [title, setTitle] = useState('');
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorderRef.current.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        setAudioBlob(blob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      setIsPaused(false);
      
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);

      toast.success('Gravação iniciada');
    } catch (error) {
      toast.error('Erro ao acessar microfone. Verifique as permissões.');
      console.error(error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      clearInterval(timerRef.current);
      toast.success('Gravação finalizada');
    }
  };

  const uploadAudio = async () => {
    if (!audioBlob) {
      toast.error('Nenhum áudio gravado');
      return;
    }

    setUploading(true);
    
    try {
      const formData = new FormData();
      formData.append('file', audioBlob, 'recording.webm');
      formData.append('title', title || `Consulta ${new Date().toLocaleDateString('pt-BR')}`);

      const response = await axios.post(`${API}/transcriptions/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      toast.success('Transcrição concluída!');
      navigate(`/transcription/${response.data.id}`);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao fazer upload');
    } finally {
      setUploading(false);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const resetRecording = () => {
    setAudioBlob(null);
    setRecordingTime(0);
    setTitle('');
  };

  return (
    <div className="recorder-page">
      <div className="recorder-container">
        <div className="recorder-header">
          <button 
            className="btn btn-secondary"
            onClick={() => navigate('/dashboard')}
            data-testid="back-to-dashboard-btn"
          >
            <ArrowLeft size={20} />
            Voltar
          </button>
        </div>

        <div className="recorder-card card fade-in" data-testid="recorder-card">
          <h1>Nova Gravação</h1>
          <p className="recorder-subtitle">Grave o áudio da consulta médica</p>

          <div className="title-input-group">
            <label htmlFor="title">Título da Consulta (Opcional)</label>
            <input
              id="title"
              type="text"
              className="input"
              placeholder="Ex: Consulta Paciente José"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              disabled={isRecording || uploading}
              data-testid="recording-title-input"
            />
          </div>

          <div className="recorder-visual">
            {isRecording && (
              <div className="recording-indicator pulse">
                <div className="recording-dot"></div>
                <span>Gravando...</span>
              </div>
            )}
            
            <div className="timer" data-testid="recording-timer">
              {formatTime(recordingTime)}
            </div>

            {isRecording && (
              <div className="audio-wave-active">
                {[...Array(7)].map((_, i) => (
                  <span key={i} className="wave-bar-active"></span>
                ))}
              </div>
            )}
          </div>

          <div className="recorder-controls">
            {!isRecording && !audioBlob && (
              <button 
                className="btn btn-primary btn-large recorder-btn"
                onClick={startRecording}
                data-testid="start-recording-btn"
              >
                <Mic size={24} />
                Iniciar Gravação
              </button>
            )}

            {isRecording && (
              <button 
                className="btn btn-danger btn-large recorder-btn"
                onClick={stopRecording}
                data-testid="stop-recording-btn"
              >
                <Square size={24} />
                Parar Gravação
              </button>
            )}

            {audioBlob && !uploading && (
              <div className="post-recording-controls">
                <button 
                  className="btn btn-primary btn-large"
                  onClick={uploadAudio}
                  data-testid="upload-audio-btn"
                >
                  <Upload size={24} />
                  Transcrever Áudio
                </button>
                <button 
                  className="btn btn-secondary"
                  onClick={resetRecording}
                  data-testid="reset-recording-btn"
                >
                  Gravar Novamente
                </button>
              </div>
            )}

            {uploading && (
              <div className="uploading-state" data-testid="uploading-state">
                <Loader size={32} className="spinner" />
                <p>Transcrevendo áudio com IA...</p>
                <p className="uploading-note">Isso pode levar alguns segundos</p>
              </div>
            )}
          </div>

          {audioBlob && !uploading && (
            <div className="audio-preview fade-in">
              <audio controls src={URL.createObjectURL(audioBlob)} />
            </div>
          )}
        </div>
      </div>

      <style jsx>{`
        .recorder-page {
          min-height: 100vh;
          padding: 2rem;
        }

        .recorder-container {
          max-width: 800px;
          margin: 0 auto;
        }

        .recorder-header {
          margin-bottom: 2rem;
        }

        .recorder-card {
          text-align: center;
          padding: 3rem;
        }

        .recorder-card h1 {
          font-size: 2.5rem;
          font-weight: 700;
          color: #0f172a;
          margin-bottom: 0.5rem;
        }

        .recorder-subtitle {
          color: #64748b;
          font-size: 1.1rem;
          margin-bottom: 2rem;
        }

        .title-input-group {
          text-align: left;
          margin-bottom: 3rem;
        }

        .title-input-group label {
          display: block;
          font-weight: 600;
          color: #334155;
          margin-bottom: 0.5rem;
        }

        .recorder-visual {
          margin: 3rem 0;
          min-height: 200px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 2rem;
        }

        .recording-indicator {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          color: #ef4444;
          font-weight: 600;
          font-size: 1.1rem;
        }

        .recording-dot {
          width: 16px;
          height: 16px;
          background: #ef4444;
          border-radius: 50%;
          animation: pulse 1.5s ease-in-out infinite;
        }

        .timer {
          font-size: 4rem;
          font-weight: 800;
          font-family: 'Manrope', sans-serif;
          background: linear-gradient(135deg, #0284c7 0%, #0ea5e9 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .audio-wave-active {
          display: flex;
          gap: 8px;
          align-items: flex-end;
          height: 80px;
        }

        .wave-bar-active {
          width: 8px;
          background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
          border-radius: 4px;
          animation: wave 1s ease-in-out infinite;
        }

        .wave-bar-active:nth-child(1) { animation-delay: 0s; }
        .wave-bar-active:nth-child(2) { animation-delay: 0.1s; }
        .wave-bar-active:nth-child(3) { animation-delay: 0.2s; }
        .wave-bar-active:nth-child(4) { animation-delay: 0.3s; }
        .wave-bar-active:nth-child(5) { animation-delay: 0.4s; }
        .wave-bar-active:nth-child(6) { animation-delay: 0.5s; }
        .wave-bar-active:nth-child(7) { animation-delay: 0.6s; }

        @keyframes wave {
          0%, 100% { height: 30%; }
          50% { height: 100%; }
        }

        .recorder-controls {
          display: flex;
          flex-direction: column;
          gap: 1rem;
          align-items: center;
        }

        .recorder-btn {
          min-width: 280px;
        }

        .post-recording-controls {
          display: flex;
          flex-direction: column;
          gap: 1rem;
          width: 100%;
          max-width: 400px;
        }

        .uploading-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 1rem;
          padding: 2rem;
        }

        .spinner {
          color: #0ea5e9;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .uploading-state p {
          color: #0f172a;
          font-weight: 600;
          font-size: 1.1rem;
        }

        .uploading-note {
          color: #64748b !important;
          font-size: 0.9rem !important;
          font-weight: 400 !important;
        }

        .audio-preview {
          margin-top: 2rem;
          padding-top: 2rem;
          border-top: 1px solid #e2e8f0;
        }

        .audio-preview audio {
          width: 100%;
          max-width: 500px;
        }
      `}</style>
    </div>
  );
}

export default Recorder;