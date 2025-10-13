import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { API } from '../App';
import axios from 'axios';
import { ArrowLeft, FileText, Brain, Loader, Clock, Download } from 'lucide-react';

function TranscriptionDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [transcription, setTranscription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [structuring, setStructuring] = useState(false);

  useEffect(() => {
    loadTranscription();
  }, [id]);

  const loadTranscription = async () => {
    try {
      const response = await axios.get(`${API}/transcriptions/${id}`);
      setTranscription(response.data);
    } catch (error) {
      toast.error('Erro ao carregar transcrição');
      navigate('/dashboard');
    } finally {
      setLoading(false);
    }
  };

  const structureNotes = async () => {
    setStructuring(true);
    
    try {
      const response = await axios.post(`${API}/transcriptions/structure`, {
        transcription_id: id
      });

      setTranscription(prev => ({
        ...prev,
        structured_notes: response.data.structured_notes,
        status: 'structured'
      }));

      toast.success('Notas estruturadas com sucesso!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao estruturar notas');
    } finally {
      setStructuring(false);
    }
  };

  const exportNotes = () => {
    if (!transcription) return;

    let content = `${transcription.title}\n`;
    content += `Data: ${new Date(transcription.created_at).toLocaleDateString('pt-BR')}\n\n`;
    
    if (transcription.structured_notes) {
      content += `ANAMNESE:\n${transcription.structured_notes.anamnese || 'N/A'}\n\n`;
      content += `EXAME FÍSICO:\n${transcription.structured_notes.exame_fisico || 'N/A'}\n\n`;
      content += `HIPÓTESE DIAGNÓSTICA:\n${transcription.structured_notes.hipotese_diagnostica || 'N/A'}\n\n`;
      content += `CONDUTA:\n${transcription.structured_notes.conduta || 'N/A'}\n\n`;
    }
    
    content += `\n--- TRANSCRIÇÃO COMPLETA ---\n${transcription.transcript_text}`;

    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${transcription.title}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    
    toast.success('Arquivo exportado!');
  };

  const formatDate = (isoString) => {
    const date = new Date(isoString);
    return date.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="loading-screen">
        <Loader size={48} className="spinner" />
        <p>Carregando transcrição...</p>
      </div>
    );
  }

  if (!transcription) return null;

  return (
    <div className="detail-page">
      <div className="detail-container">
        <div className="detail-header">
          <button 
            className="btn btn-secondary"
            onClick={() => navigate('/dashboard')}
            data-testid="back-btn"
          >
            <ArrowLeft size={20} />
            Voltar
          </button>
          
          <button 
            className="btn btn-primary"
            onClick={exportNotes}
            data-testid="export-btn"
          >
            <Download size={20} />
            Exportar
          </button>
        </div>

        <div className="detail-content fade-in">
          <div className="content-header">
            <div>
              <h1 data-testid="transcription-title">{transcription.title}</h1>
              <div className="meta-info">
                <span>
                  <Clock size={16} />
                  {formatDate(transcription.created_at)}
                </span>
              </div>
            </div>
          </div>

          {/* Structured Notes Section */}
          {transcription.structured_notes ? (
            <div className="structured-section card" data-testid="structured-notes">
              <div className="section-header-with-icon">
                <Brain size={24} />
                <h2>Notas Clínicas Estruturadas</h2>
              </div>

              <div className="clinical-sections">
                <div className="clinical-section">
                  <h3>Anamnese</h3>
                  <p data-testid="anamnese-content">{transcription.structured_notes.anamnese || 'Nenhuma informação disponível'}</p>
                </div>

                <div className="clinical-section">
                  <h3>Exame Físico</h3>
                  <p data-testid="exame-fisico-content">{transcription.structured_notes.exame_fisico || 'Nenhuma informação disponível'}</p>
                </div>

                <div className="clinical-section">
                  <h3>Hipótese Diagnóstica</h3>
                  <p data-testid="hipotese-diagnostica-content">{transcription.structured_notes.hipotese_diagnostica || 'Nenhuma informação disponível'}</p>
                </div>

                <div className="clinical-section">
                  <h3>Conduta</h3>
                  <p data-testid="conduta-content">{transcription.structured_notes.conduta || 'Nenhuma informação disponível'}</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="structure-prompt card" data-testid="structure-prompt">
              <Brain size={48} />
              <h3>Estruturar Notas Clínicas</h3>
              <p>Use IA para organizar a transcrição em seções clínicas estruturadas</p>
              <button 
                className="btn btn-primary"
                onClick={structureNotes}
                disabled={structuring}
                data-testid="structure-notes-btn"
              >
                {structuring ? (
                  <>
                    <Loader size={20} className="spinner" />
                    Estruturando...
                  </>
                ) : (
                  <>
                    <Brain size={20} />
                    Estruturar com IA
                  </>
                )}
              </button>
            </div>
          )}

          {/* Transcript Section */}
          <div className="transcript-section card">
            <div className="section-header-with-icon">
              <FileText size={24} />
              <h2>Transcrição Completa</h2>
            </div>
            <div className="transcript-content" data-testid="transcript-content">
              <p>{transcription.transcript_text}</p>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        .detail-page {
          min-height: 100vh;
          padding: 2rem;
        }

        .detail-container {
          max-width: 1000px;
          margin: 0 auto;
        }

        .detail-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 2rem;
        }

        .detail-content {
          display: flex;
          flex-direction: column;
          gap: 2rem;
        }

        .content-header h1 {
          font-size: 2.5rem;
          font-weight: 700;
          color: #0f172a;
          margin-bottom: 1rem;
        }

        .meta-info {
          display: flex;
          align-items: center;
          gap: 1rem;
          color: #64748b;
          font-size: 0.95rem;
        }

        .meta-info span {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .section-header-with-icon {
          display: flex;
          align-items: center;
          gap: 1rem;
          margin-bottom: 2rem;
          padding-bottom: 1rem;
          border-bottom: 2px solid #e2e8f0;
        }

        .section-header-with-icon svg {
          color: #0ea5e9;
        }

        .section-header-with-icon h2 {
          font-size: 1.75rem;
          font-weight: 700;
          color: #0f172a;
        }

        .structured-section {
          padding: 2.5rem;
        }

        .clinical-sections {
          display: flex;
          flex-direction: column;
          gap: 2rem;
        }

        .clinical-section {
          padding: 1.5rem;
          background: rgba(14, 165, 233, 0.05);
          border-radius: 12px;
          border-left: 4px solid #0ea5e9;
        }

        .clinical-section h3 {
          font-size: 1.2rem;
          font-weight: 700;
          color: #0284c7;
          margin-bottom: 0.75rem;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .clinical-section p {
          color: #334155;
          line-height: 1.8;
          white-space: pre-wrap;
        }

        .structure-prompt {
          padding: 3rem;
          text-align: center;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 1.5rem;
        }

        .structure-prompt svg {
          color: #0ea5e9;
          opacity: 0.7;
        }

        .structure-prompt h3 {
          font-size: 1.5rem;
          font-weight: 700;
          color: #0f172a;
        }

        .structure-prompt p {
          color: #64748b;
          font-size: 1.05rem;
        }

        .transcript-section {
          padding: 2.5rem;
        }

        .transcript-content {
          background: rgba(248, 250, 252, 0.8);
          padding: 2rem;
          border-radius: 12px;
          border: 1px solid #e2e8f0;
        }

        .transcript-content p {
          color: #334155;
          line-height: 1.9;
          font-size: 1.05rem;
          white-space: pre-wrap;
        }

        .spinner {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        @media (max-width: 768px) {
          .content-header h1 {
            font-size: 1.75rem;
          }

          .detail-header {
            flex-direction: column;
            gap: 1rem;
          }
        }
      `}</style>
    </div>
  );
}

export default TranscriptionDetail;