import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { API } from '../App';
import axios from 'axios';
import { Users, Clock, Shield, Calendar, Plus, CheckCircle, XCircle } from 'lucide-react';

function AdminPanel({ user }) {
  const navigate = useNavigate();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // all, active, expired

  useEffect(() => {
    if (!user.is_admin) {
      toast.error('Acesso negado');
      navigate('/dashboard');
      return;
    }
    loadUsers();
  }, [user, navigate]);

  const loadUsers = async () => {
    try {
      const response = await axios.get(`${API}/admin/users`);
      setUsers(response.data);
    } catch (error) {
      toast.error('Erro ao carregar usuários');
    } finally {
      setLoading(false);
    }
  };

  const renewSubscription = async (userId, months = 1) => {
    try {
      await axios.put(`${API}/admin/users/${userId}/subscription`, { months });
      toast.success(`Assinatura renovada por ${months} mês(es)`);
      loadUsers();
    } catch (error) {
      toast.error('Erro ao renovar assinatura');
    }
  };

  const toggleAdminStatus = async (userId) => {
    try {
      await axios.put(`${API}/admin/users/${userId}/admin-status`);
      toast.success('Status de admin atualizado');
      loadUsers();
    } catch (error) {
      toast.error('Erro ao atualizar status');
    }
  };

  const getStatusInfo = (status) => {
    const statusMap = {
      active: { label: 'Ativo', color: '#10b981', icon: <CheckCircle size={16} /> },
      grace_period: { label: 'Período de Graça', color: '#f59e0b', icon: <Clock size={16} /> },
      expired: { label: 'Expirado', color: '#ef4444', icon: <XCircle size={16} /> }
    };
    return statusMap[status] || statusMap.expired;
  };

  const getDaysRemaining = (endDate) => {
    if (!endDate) return 0;
    const end = new Date(endDate);
    const now = new Date();
    const diff = Math.ceil((end - now) / (1000 * 60 * 60 * 24));
    return diff;
  };

  const filteredUsers = users.filter(u => {
    if (filter === 'all') return true;
    return u.subscription_status === filter;
  });

  if (loading) {
    return <div className="loading-screen">Carregando...</div>;
  }

  return (
    <div className="admin-panel">
      <nav className="dashboard-nav">
        <div className="nav-content">
          <h2 className="nav-logo">AudioMedic Admin</h2>
          <div className="nav-actions">
            <button 
              className="btn btn-secondary"
              onClick={() => navigate('/dashboard')}
              data-testid="back-to-dashboard-btn"
            >
              Voltar ao Dashboard
            </button>
          </div>
        </div>
      </nav>

      <div className="admin-container">
        <div className="admin-header fade-in">
          <div>
            <h1 data-testid="admin-title">
              <Shield size={32} />
              Gerenciar Usuários
            </h1>
            <p>Controle de assinaturas e permissões</p>
          </div>
          
          <div className="stats-cards">
            <div className="stat-card">
              <Users size={24} />
              <div>
                <span className="stat-value">{users.length}</span>
                <span className="stat-label">Total</span>
              </div>
            </div>
            <div className="stat-card stat-active">
              <CheckCircle size={24} />
              <div>
                <span className="stat-value">{users.filter(u => u.subscription_status === 'active').length}</span>
                <span className="stat-label">Ativos</span>
              </div>
            </div>
            <div className="stat-card stat-expired">
              <XCircle size={24} />
              <div>
                <span className="stat-value">{users.filter(u => u.subscription_status === 'expired').length}</span>
                <span className="stat-label">Expirados</span>
              </div>
            </div>
          </div>
        </div>

        <div className="filter-tabs">
          <button 
            className={`filter-tab ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
            data-testid="filter-all"
          >
            Todos ({users.length})
          </button>
          <button 
            className={`filter-tab ${filter === 'active' ? 'active' : ''}`}
            onClick={() => setFilter('active')}
            data-testid="filter-active"
          >
            Ativos ({users.filter(u => u.subscription_status === 'active').length})
          </button>
          <button 
            className={`filter-tab ${filter === 'grace_period' ? 'active' : ''}`}
            onClick={() => setFilter('grace_period')}
            data-testid="filter-grace"
          >
            Graça ({users.filter(u => u.subscription_status === 'grace_period').length})
          </button>
          <button 
            className={`filter-tab ${filter === 'expired' ? 'active' : ''}`}
            onClick={() => setFilter('expired')}
            data-testid="filter-expired"
          >
            Expirados ({users.filter(u => u.subscription_status === 'expired').length})
          </button>
        </div>

        <div className="users-table-container card">
          <table className="users-table" data-testid="users-table">
            <thead>
              <tr>
                <th>Usuário</th>
                <th>Email</th>
                <th>Status</th>
                <th>Vencimento</th>
                <th>Dias Restantes</th>
                <th>Admin</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {filteredUsers.map((u, index) => {
                const statusInfo = getStatusInfo(u.subscription_status);
                const daysRemaining = getDaysRemaining(u.subscription_end_date);
                
                return (
                  <tr key={u.id} className="fade-in" style={{ animationDelay: `${index * 0.05}s` }}>
                    <td>
                      <div className="user-cell">
                        <div className="user-avatar">{u.name.charAt(0).toUpperCase()}</div>
                        <span className="user-name">{u.name}</span>
                      </div>
                    </td>
                    <td>{u.email}</td>
                    <td>
                      <span 
                        className="status-badge"
                        style={{ backgroundColor: `${statusInfo.color}20`, color: statusInfo.color }}
                      >
                        {statusInfo.icon}
                        {statusInfo.label}
                      </span>
                    </td>
                    <td>
                      {u.subscription_end_date ? 
                        new Date(u.subscription_end_date).toLocaleDateString('pt-BR') : 
                        'N/A'
                      }
                    </td>
                    <td>
                      <span className={daysRemaining < 0 ? 'text-danger' : daysRemaining < 7 ? 'text-warning' : ''}>
                        {daysRemaining < 0 ? `${Math.abs(daysRemaining)} dias atraso` : `${daysRemaining} dias`}
                      </span>
                    </td>
                    <td>
                      <button
                        className={`btn-icon ${u.is_admin ? 'active' : ''}`}
                        onClick={() => toggleAdminStatus(u.id)}
                        title={u.is_admin ? 'Remover admin' : 'Tornar admin'}
                        data-testid={`toggle-admin-${index}`}
                      >
                        <Shield size={18} />
                      </button>
                    </td>
                    <td>
                      <div className="action-buttons">
                        <button
                          className="btn btn-primary btn-small"
                          onClick={() => renewSubscription(u.id, 1)}
                          data-testid={`renew-1m-${index}`}
                        >
                          <Plus size={16} />
                          1 Mês
                        </button>
                        <button
                          className="btn btn-secondary btn-small"
                          onClick={() => renewSubscription(u.id, 3)}
                          data-testid={`renew-3m-${index}`}
                        >
                          <Plus size={16} />
                          3 Meses
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <style jsx>{`
        .admin-panel {
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
          max-width: 1600px;
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

        .admin-container {
          max-width: 1600px;
          margin: 0 auto;
          padding: 3rem 2rem;
        }

        .admin-header {
          margin-bottom: 3rem;
        }

        .admin-header h1 {
          font-size: 2.5rem;
          font-weight: 700;
          color: #0f172a;
          display: flex;
          align-items: center;
          gap: 1rem;
          margin-bottom: 0.5rem;
        }

        .admin-header p {
          color: #64748b;
          font-size: 1.1rem;
        }

        .stats-cards {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 1.5rem;
          margin-top: 2rem;
        }

        .stat-card {
          background: rgba(255, 255, 255, 0.9);
          backdrop-filter: blur(20px);
          padding: 1.5rem;
          border-radius: 16px;
          border: 1px solid rgba(14, 165, 233, 0.1);
          display: flex;
          align-items: center;
          gap: 1rem;
        }

        .stat-card svg {
          color: #0ea5e9;
        }

        .stat-card.stat-active svg {
          color: #10b981;
        }

        .stat-card.stat-expired svg {
          color: #ef4444;
        }

        .stat-value {
          font-size: 2rem;
          font-weight: 800;
          color: #0f172a;
          display: block;
        }

        .stat-label {
          font-size: 0.9rem;
          color: #64748b;
        }

        .filter-tabs {
          display: flex;
          gap: 1rem;
          margin-bottom: 2rem;
          border-bottom: 2px solid #e2e8f0;
          padding-bottom: 0;
        }

        .filter-tab {
          background: none;
          border: none;
          padding: 1rem 1.5rem;
          font-weight: 600;
          color: #64748b;
          cursor: pointer;
          transition: all 0.3s ease;
          border-bottom: 3px solid transparent;
          margin-bottom: -2px;
        }

        .filter-tab:hover {
          color: #0ea5e9;
        }

        .filter-tab.active {
          color: #0ea5e9;
          border-bottom-color: #0ea5e9;
        }

        .users-table-container {
          overflow-x: auto;
          padding: 0;
        }

        .users-table {
          width: 100%;
          border-collapse: collapse;
        }

        .users-table thead {
          background: rgba(14, 165, 233, 0.05);
        }

        .users-table th {
          text-align: left;
          padding: 1.25rem 1rem;
          font-weight: 700;
          color: #0f172a;
          font-size: 0.9rem;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .users-table td {
          padding: 1.25rem 1rem;
          border-bottom: 1px solid #e2e8f0;
        }

        .users-table tbody tr:hover {
          background: rgba(14, 165, 233, 0.02);
        }

        .user-cell {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .user-avatar {
          width: 40px;
          height: 40px;
          border-radius: 50%;
          background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 700;
          font-size: 1.1rem;
        }

        .user-name {
          font-weight: 600;
          color: #0f172a;
        }

        .status-badge {
          display: inline-flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.5rem 1rem;
          border-radius: 20px;
          font-size: 0.85rem;
          font-weight: 600;
        }

        .text-danger {
          color: #ef4444;
          font-weight: 600;
        }

        .text-warning {
          color: #f59e0b;
          font-weight: 600;
        }

        .btn-icon {
          background: rgba(148, 163, 184, 0.1);
          border: 2px solid transparent;
          width: 36px;
          height: 36px;
          border-radius: 8px;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: all 0.3s ease;
          color: #64748b;
        }

        .btn-icon:hover {
          background: rgba(14, 165, 233, 0.1);
          color: #0ea5e9;
        }

        .btn-icon.active {
          background: rgba(14, 165, 233, 0.2);
          border-color: #0ea5e9;
          color: #0ea5e9;
        }

        .action-buttons {
          display: flex;
          gap: 0.5rem;
        }

        .btn-small {
          padding: 0.5rem 1rem;
          font-size: 0.85rem;
        }

        @media (max-width: 1200px) {
          .users-table {
            font-size: 0.9rem;
          }

          .users-table th,
          .users-table td {
            padding: 1rem 0.75rem;
          }
        }
      `}</style>
    </div>
  );
}

export default AdminPanel;