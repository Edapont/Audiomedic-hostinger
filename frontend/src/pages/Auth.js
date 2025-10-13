import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { API } from '../App';
import axios from 'axios';
import { Mail, Lock, User, LogIn, UserPlus } from 'lucide-react';

function Auth({ onLogin }) {
  const navigate = useNavigate();
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (isLogin) {
        const response = await axios.post(`${API}/auth/login`, {
          email: formData.email,
          password: formData.password
        });
        
        toast.success('Login realizado com sucesso!');
        onLogin(response.data.token, response.data.user);
        navigate('/dashboard');
      } else {
        await axios.post(`${API}/auth/register`, {
          email: formData.email,
          password: formData.password,
          name: formData.name
        });
        
        toast.success('Conta criada! Faça login para continuar.');
        setIsLogin(true);
        setFormData({ email: formData.email, password: '', name: '' });
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao processar solicitação');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-container fade-in">
        <div className="auth-card card">
          <div className="auth-header">
            <h1 data-testid="auth-title">{isLogin ? 'Bem-vindo de Volta' : 'Criar Conta'}</h1>
            <p>{isLogin ? 'Entre para continuar' : 'Cadastre-se gratuitamente'}</p>
          </div>

          <form onSubmit={handleSubmit} className="auth-form" data-testid="auth-form">
            {!isLogin && (
              <div className="form-group">
                <label htmlFor="name">
                  <User size={18} />
                  Nome Completo
                </label>
                <input
                  id="name"
                  type="text"
                  className="input"
                  placeholder="Dr. João Silva"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required={!isLogin}
                  data-testid="name-input"
                />
              </div>
            )}

            <div className="form-group">
              <label htmlFor="email">
                <Mail size={18} />
                Email
              </label>
              <input
                id="email"
                type="email"
                className="input"
                placeholder="seu@email.com"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
                data-testid="email-input"
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">
                <Lock size={18} />
                Senha
              </label>
              <input
                id="password"
                type="password"
                className="input"
                placeholder="••••••••"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                required
                minLength={6}
                data-testid="password-input"
              />
            </div>

            <button 
              type="submit" 
              className="btn btn-primary btn-full"
              disabled={loading}
              data-testid="auth-submit-btn"
            >
              {loading ? 'Processando...' : (
                <>
                  {isLogin ? <LogIn size={20} /> : <UserPlus size={20} />}
                  {isLogin ? 'Entrar' : 'Criar Conta'}
                </>
              )}
            </button>
          </form>

          <div className="auth-switch">
            <p>
              {isLogin ? 'Não tem uma conta?' : 'Já tem uma conta?'}
              <button 
                onClick={() => setIsLogin(!isLogin)}
                className="switch-btn"
                data-testid="toggle-auth-mode-btn"
              >
                {isLogin ? 'Cadastre-se' : 'Faça login'}
              </button>
            </p>
          </div>
        </div>
      </div>

      <style jsx>{`
        .auth-page {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 2rem;
        }

        .auth-container {
          width: 100%;
          max-width: 480px;
        }

        .auth-card {
          padding: 3rem;
        }

        .auth-header {
          text-align: center;
          margin-bottom: 2.5rem;
        }

        .auth-header h1 {
          font-size: 2rem;
          font-weight: 700;
          color: #0f172a;
          margin-bottom: 0.5rem;
        }

        .auth-header p {
          color: #64748b;
          font-size: 1rem;
        }

        .auth-form {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }

        .form-group {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .form-group label {
          font-weight: 600;
          color: #334155;
          font-size: 0.9rem;
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .btn-full {
          width: 100%;
          justify-content: center;
          margin-top: 0.5rem;
        }

        .auth-switch {
          margin-top: 2rem;
          text-align: center;
          padding-top: 2rem;
          border-top: 1px solid #e2e8f0;
        }

        .auth-switch p {
          color: #64748b;
          font-size: 0.95rem;
        }

        .switch-btn {
          background: none;
          border: none;
          color: #0ea5e9;
          font-weight: 600;
          cursor: pointer;
          margin-left: 0.5rem;
          transition: color 0.3s ease;
        }

        .switch-btn:hover {
          color: #0284c7;
          text-decoration: underline;
        }
      `}</style>
    </div>
  );
}

export default Auth;