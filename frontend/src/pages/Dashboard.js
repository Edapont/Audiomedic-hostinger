import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { API } from '../App';
import axios from 'axios';
import { Mic, FileText, LogOut, Plus, Clock, Trash2, Eye, Shield, AlertCircle, CheckCircle } from 'lucide-react';

function Dashboard({ user, onLogout }) {
  const navigate = useNavigate();
  const [transcriptions, setTranscriptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [userInfo, setUserInfo] = useState(user);

  useEffect(() => {
    loadTranscriptions();
    loadUserInfo();
  }, []);

  const loadUserInfo = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUserInfo(response.data);
    } catch (error) {
      console.error('Error loading user info:', error);
    }
  };

  const getDaysUntilExpiry = () => {
    if (!userInfo?.subscription_end_date) return 0;
    const end = new Date(userInfo.subscription_end_date);
    const now = new Date();
    return Math.ceil((end - now) / (1000 * 60 * 60 * 24));
  };

  const getSubscriptionBanner = () => {
    const status = userInfo?.subscription_status;
    const days = getDaysUntilExpiry();

    if (status === 'expired') {
      return {
        show: true,
        type: 'danger',
        icon: <AlertCircle size={20} />,
        message: 'Assinatura expirada. Você está em modo leitura. Entre em contato com o administrador.',
        bgColor: 'rgba(239, 68, 68, 0.1)',
        borderColor: '#ef4444',
        textColor: '#dc2626'
      };
    }

    if (status === 'grace_period') {
      return {
        show: true,
        type: 'warning',
        icon: <Clock size={20} />,
        message: `Período de graça: ${Math.abs(days)} dias restantes antes do modo leitura.`,
        bgColor: 'rgba(245, 158, 11, 0.1)',
        borderColor: '#f59e0b',
        textColor: '#d97706'
      };
    }

    if (status === 'active' && days <= 7 && days > 0) {
      return {
        show: true,
        type: 'info',
        icon: <AlertCircle size={20} />,
        message: `Sua assinatura vence em ${days} dia${days > 1 ? 's' : ''}.`,
        bgColor: 'rgba(14, 165, 233, 0.1)',
        borderColor: '#0ea5e9',
        textColor: '#0284c7'
      };
    }

    return { show: false };
  };

  const canCreateNew = userInfo?.subscription_status === 'active' || userInfo?.subscription_status === 'grace_period';

  const loadTranscriptions = async () => {
    try {
      const response = await axios.get(`${API}/transcriptions`);
      setTranscriptions(response.data);
    } catch (error) {
      toast.error('Erro ao carregar transcrições');
    } finally {
      setLoading(false);
    }
  };

  const deleteTranscription = async (id) => {
    if (!window.confirm('Tem certeza que deseja excluir esta transcrição?')) return;
    
    try {
      await axios.delete(`${API}/transcriptions/${id}`);
      toast.success('Transcrição excluída');
      loadTranscriptions();
    } catch (error) {
      toast.error('Erro ao excluir transcrição');
    }
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

  const getStatusBadge = (status) => {
    const badges = {
      'transcribed': { label: 'Transcrito', color: '#0ea5e9' },
      'structured': { label: 'Estruturado', color: '#10b981' }
    };
    const badge = badges[status] || { label: status, color: '#64748b' };
    return (
      <span className="status-badge" style={{ backgroundColor: `${badge.color}20`, color: badge.color }}>
        {badge.label}
      </span>
    );
  };

  return (
    <div className="dashboard-page">
      <nav className="dashboard-nav">
        <div className="nav-content">
          <h2 className="nav-logo" data-testid="dashboard-title">AudioMedic</h2>
          <div className="nav-actions">
            <span className="user-name" data-testid="user-name">Dr. {user.name}</span>
            {userInfo?.is_admin && (
              <button 
                className="btn btn-secondary"
                onClick={() => navigate('/admin')}
                data-testid="admin-panel-btn"
              >
                <Shield size={18} />
                Admin
              </button>
            )}
            <button 
              className="btn btn-secondary"
              onClick={onLogout}
              data-testid="logout-btn"
            >
              <LogOut size={18} />
              Sair
            </button>
          </div>
        </div>
      </nav>

      <div className="dashboard-container">
        {/* Subscription Banner */}
        {(() => {
          const banner = getSubscriptionBanner();
          if (!banner.show) return null;
          
          return (
            <div 
              className="subscription-banner fade-in"
              style={{
                backgroundColor: banner.bgColor,
                borderLeft: `4px solid ${banner.borderColor}`,
                color: banner.textColor
              }}
              data-testid="subscription-banner"
            >
              {banner.icon}
              <span>{banner.message}</span>
            </div>
          );
        })()}

        <div className="dashboard-header fade-in">
          <div>
            <h1>Minhas Transcrições</h1>
            <p>Gerencie suas consultas e anotações médicas</p>
          </div>
          <button 
            className="btn btn-primary"
            onClick={() => {
              if (!canCreateNew) {
                toast.error('Assinatura expirada. Renove para criar novas transcrições.');
                return;
              }
              navigate('/recorder');
            }}
            disabled={!canCreateNew}
            data-testid="new-recording-btn"
          >
            <Plus size={20} />
            Nova Gravação
          </button>
        </div>

        {loading ? (
          <div className="loading-state">
            <div className="pulse">Carregando...</div>
          </div>
        ) : transcriptions.length === 0 ? (
          <div className="empty-state card fade-in" data-testid="empty-state">
            <Mic size={64} strokeWidth={1.5} />
            <h3>Nenhuma transcrição ainda</h3>
            <p>Comece gravando sua primeira consulta médica</p>
            <button 
              className="btn btn-primary"
              onClick={() => navigate('/recorder')}
              data-testid="empty-state-record-btn"
            >
              <Mic size={20} />
              Gravar Agora
            </button>
          </div>
        ) : (
          <div className="transcriptions-grid">
            {transcriptions.map((transcription, index) => (
              <div 
                key={transcription.id} 
                className="transcription-card card fade-in"
                style={{ animationDelay: `${index * 0.05}s` }}
                data-testid={`transcription-card-${index}`}
              >
                <div className="card-header">
                  <div className="card-icon">
                    <FileText size={24} />
                  </div>
                  <div className="card-title">
                    <h3>{transcription.title}</h3>
                    {getStatusBadge(transcription.status)}
                  </div>
                </div>
                
                <div className="card-meta">
                  <span>
                    <Clock size={16} />
                    {formatDate(transcription.created_at)}
                  </span>
                </div>

                {transcription.transcript_text && (
                  <p className="card-preview">
                    {transcription.transcript_text.substring(0, 150)}...
                  </p>
                )}

                <div className="card-actions">
                  <button 
                    className="btn btn-secondary btn-small"
                    onClick={() => navigate(`/transcription/${transcription.id}`)}
                    data-testid={`view-transcription-btn-${index}`}
                  >
                    <Eye size={16} />
                    Visualizar
                  </button>
                  <button 
                    className="btn btn-danger btn-small"
                    onClick={() => deleteTranscription(transcription.id)}
                    data-testid={`delete-transcription-btn-${index}`}
                  >
                    <Trash2 size={16} />
                    Excluir
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <style jsx>{`
        .dashboard-page {
          min-height: 100vh;
        }

        .dashboard-nav {
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(20px);
          border-bottom: 1px solid rgba(14, 165, 233, 0.1);
          padding: 1rem 2rem;
          position: sticky;
          top: 0;
          z-index: 100;
        }

        .nav-content {
          max-width: 1400px;
          margin: 0 auto;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .nav-logo {
          font-size: 1.5rem;
          font-weight: 800;
          background: linear-gradient(135deg, #0284c7 0%, #0ea5e9 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .nav-actions {
          display: flex;
          align-items: center;
          gap: 1.5rem;
        }

        .user-name {
          font-weight: 600;
          color: #0f172a;
        }

        .subscription-banner {
          padding: 1.25rem 1.5rem;
          border-radius: 12px;
          margin-bottom: 2rem;
          display: flex;
          align-items: center;
          gap: 1rem;
          font-weight: 600;
          font-size: 0.95rem;
        }

        .dashboard-container {
          max-width: 1400px;
          margin: 0 auto;
          padding: 3rem 2rem;
        }

        .dashboard-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 3rem;
          flex-wrap: wrap;
          gap: 1.5rem;
        }

        .dashboard-header h1 {
          font-size: 2.5rem;
          font-weight: 700;
          color: #0f172a;
          margin-bottom: 0.5rem;
        }

        .dashboard-header p {
          color: #64748b;
          font-size: 1.1rem;
        }

        .loading-state {
          text-align: center;
          padding: 4rem 2rem;
          font-size: 1.2rem;
          color: #0369a1;
        }

        .empty-state {
          text-align: center;
          padding: 4rem 2rem;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 1.5rem;
        }

        .empty-state svg {
          color: #0ea5e9;
          opacity: 0.5;
        }

        .empty-state h3 {
          font-size: 1.5rem;
          font-weight: 700;
          color: #0f172a;
        }

        .empty-state p {
          color: #64748b;
          font-size: 1.1rem;
        }

        .transcriptions-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
          gap: 1.5rem;
        }

        .transcription-card {
          padding: 1.75rem;
          transition: all 0.3s ease;
          cursor: pointer;
        }

        .transcription-card:hover {
          transform: translateY(-4px);
          box-shadow: 0 12px 40px rgba(14, 165, 233, 0.15);
        }

        .card-header {
          display: flex;
          gap: 1rem;
          margin-bottom: 1rem;
        }

        .card-icon {
          width: 50px;
          height: 50px;
          background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
          color: white;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }

        .card-title {
          flex: 1;
        }

        .card-title h3 {
          font-size: 1.2rem;
          font-weight: 700;
          color: #0f172a;
          margin-bottom: 0.5rem;
        }

        .status-badge {
          display: inline-block;
          padding: 0.25rem 0.75rem;
          border-radius: 20px;
          font-size: 0.8rem;
          font-weight: 600;
        }

        .card-meta {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          color: #64748b;
          font-size: 0.9rem;
          margin-bottom: 1rem;
        }

        .card-preview {
          color: #475569;
          line-height: 1.6;
          margin-bottom: 1.5rem;
          font-size: 0.95rem;
        }

        .card-actions {
          display: flex;
          gap: 0.75rem;
          padding-top: 1rem;
          border-top: 1px solid #e2e8f0;
        }

        .btn-small {
          padding: 0.5rem 1rem;
          font-size: 0.9rem;
        }

        @media (max-width: 768px) {
          .dashboard-header {
            flex-direction: column;
            align-items: flex-start;
          }

          .transcriptions-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
}

export default Dashboard;