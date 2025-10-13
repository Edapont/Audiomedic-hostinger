import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mic, FileText, Brain, Shield, Clock, CheckCircle } from 'lucide-react';

function Landing() {
  const navigate = useNavigate();

  const features = [
    {
      icon: <Mic size={32} />,
      title: 'Gravação Inteligente',
      description: 'Capture áudio de consultas médicas diretamente do navegador com qualidade profissional'
    },
    {
      icon: <FileText size={32} />,
      title: 'Transcrição Automática',
      description: 'Transcrição precisa em português usando tecnologia OpenAI Whisper'
    },
    {
      icon: <Brain size={32} />,
      title: 'Estruturação Clínica',
      description: 'IA organiza automaticamente em: Anamnese, Exame Físico, Diagnóstico e Conduta'
    },
    {
      icon: <Shield size={32} />,
      title: 'Segurança LGPD',
      description: 'Criptografia completa e exclusão automática de áudios após transcrição'
    },
    {
      icon: <Clock size={32} />,
      title: 'Economia de Tempo',
      description: 'Reduza em até 70% o tempo gasto com anotações durante consultas'
    },
    {
      icon: <CheckCircle size={32} />,
      title: 'Prontuários Completos',
      description: 'Gere documentação clínica completa e editável em segundos'
    }
  ];

  return (
    <div className="landing-page">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <div className="hero-text fade-in">
            <h1 data-testid="landing-title">AudioMedic</h1>
            <p className="hero-subtitle">Transcrição Inteligente para Consultas Médicas</p>
            <p className="hero-description">
              Transforme áudios de consultas em anotações clínicas estruturadas automaticamente.
              Mais tempo para o paciente, menos tempo com papelada.
            </p>
            <div className="hero-buttons">
              <button 
                className="btn btn-primary btn-large"
                onClick={() => navigate('/auth')}
                data-testid="get-started-btn"
              >
                Começar Agora
              </button>
              <button 
                className="btn btn-secondary btn-large"
                onClick={() => document.getElementById('features').scrollIntoView({ behavior: 'smooth' })}
                data-testid="learn-more-btn"
              >
                Saiba Mais
              </button>
            </div>
          </div>
          
          <div className="hero-visual fade-in">
            <div className="hero-card">
              <div className="audio-wave">
                <span className="wave-bar"></span>
                <span className="wave-bar"></span>
                <span className="wave-bar"></span>
                <span className="wave-bar"></span>
                <span className="wave-bar"></span>
              </div>
              <p className="visual-label">Gravando consulta...</p>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="features-section">
        <div className="section-header fade-in">
          <h2>Recursos Principais</h2>
          <p>Tecnologia de ponta para facilitar seu dia a dia médico</p>
        </div>
        
        <div className="features-grid">
          {features.map((feature, index) => (
            <div key={index} className="feature-card fade-in" style={{ animationDelay: `${index * 0.1}s` }}>
              <div className="feature-icon">{feature.icon}</div>
              <h3>{feature.title}</h3>
              <p>{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How it Works */}
      <section className="how-it-works-section">
        <div className="section-header fade-in">
          <h2>Como Funciona</h2>
          <p>Simples, rápido e eficiente</p>
        </div>
        
        <div className="steps-container">
          <div className="step fade-in">
            <div className="step-number">1</div>
            <h3>Grave a Consulta</h3>
            <p>Clique em gravar durante a consulta médica</p>
          </div>
          
          <div className="step-arrow">→</div>
          
          <div className="step fade-in" style={{ animationDelay: '0.2s' }}>
            <div className="step-number">2</div>
            <h3>Transcrição Automática</h3>
            <p>IA transcreve o áudio em tempo real</p>
          </div>
          
          <div className="step-arrow">→</div>
          
          <div className="step fade-in" style={{ animationDelay: '0.4s' }}>
            <div className="step-number">3</div>
            <h3>Estruturação Clínica</h3>
            <p>Notas organizadas em formato médico</p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="cta-content fade-in">
          <h2>Pronto para Transformar suas Consultas?</h2>
          <p>Junte-se a médicos que já economizam horas de trabalho</p>
          <button 
            className="btn btn-primary btn-large"
            onClick={() => navigate('/auth')}
            data-testid="cta-start-btn"
          >
            Começar Gratuitamente
          </button>
        </div>
      </section>

      <style jsx>{`
        .landing-page {
          min-height: 100vh;
        }

        .hero-section {
          padding: 4rem 2rem;
          max-width: 1400px;
          margin: 0 auto;
          min-height: 90vh;
          display: flex;
          align-items: center;
        }

        .hero-content {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 4rem;
          align-items: center;
        }

        .hero-text h1 {
          font-size: 4.5rem;
          font-weight: 800;
          background: linear-gradient(135deg, #0284c7 0%, #0ea5e9 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          margin-bottom: 1rem;
          line-height: 1.1;
        }

        .hero-subtitle {
          font-size: 1.5rem;
          color: #475569;
          margin-bottom: 1.5rem;
          font-weight: 600;
        }

        .hero-description {
          font-size: 1.1rem;
          color: #64748b;
          line-height: 1.7;
          margin-bottom: 2.5rem;
        }

        .hero-buttons {
          display: flex;
          gap: 1rem;
          flex-wrap: wrap;
        }

        .btn-large {
          padding: 1rem 2.5rem;
          font-size: 1.05rem;
        }

        .hero-visual {
          display: flex;
          justify-content: center;
          align-items: center;
        }

        .hero-card {
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(20px);
          padding: 3rem;
          border-radius: 24px;
          box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
          border: 1px solid rgba(255, 255, 255, 0.8);
        }

        .audio-wave {
          display: flex;
          gap: 8px;
          justify-content: center;
          align-items: flex-end;
          height: 120px;
          margin-bottom: 1.5rem;
        }

        .wave-bar {
          width: 8px;
          background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
          border-radius: 4px;
          animation: wave 1.2s ease-in-out infinite;
        }

        .wave-bar:nth-child(1) { animation-delay: 0s; height: 40%; }
        .wave-bar:nth-child(2) { animation-delay: 0.1s; height: 70%; }
        .wave-bar:nth-child(3) { animation-delay: 0.2s; height: 100%; }
        .wave-bar:nth-child(4) { animation-delay: 0.3s; height: 60%; }
        .wave-bar:nth-child(5) { animation-delay: 0.4s; height: 50%; }

        @keyframes wave {
          0%, 100% { transform: scaleY(1); }
          50% { transform: scaleY(0.3); }
        }

        .visual-label {
          text-align: center;
          color: #0284c7;
          font-weight: 600;
          font-size: 1.1rem;
        }

        .features-section {
          padding: 6rem 2rem;
          background: rgba(255, 255, 255, 0.5);
        }

        .section-header {
          text-align: center;
          margin-bottom: 4rem;
        }

        .section-header h2 {
          font-size: 3rem;
          font-weight: 700;
          color: #0f172a;
          margin-bottom: 1rem;
        }

        .section-header p {
          font-size: 1.2rem;
          color: #64748b;
        }

        .features-grid {
          max-width: 1200px;
          margin: 0 auto;
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
          gap: 2rem;
        }

        .feature-card {
          background: rgba(255, 255, 255, 0.9);
          backdrop-filter: blur(20px);
          padding: 2.5rem;
          border-radius: 20px;
          border: 1px solid rgba(14, 165, 233, 0.1);
          transition: all 0.4s ease;
        }

        .feature-card:hover {
          transform: translateY(-8px);
          box-shadow: 0 12px 40px rgba(14, 165, 233, 0.2);
          border-color: rgba(14, 165, 233, 0.3);
        }

        .feature-icon {
          width: 70px;
          height: 70px;
          background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
          color: white;
          border-radius: 16px;
          display: flex;
          align-items: center;
          justify-content: center;
          margin-bottom: 1.5rem;
        }

        .feature-card h3 {
          font-size: 1.4rem;
          font-weight: 700;
          color: #0f172a;
          margin-bottom: 0.75rem;
        }

        .feature-card p {
          color: #64748b;
          line-height: 1.7;
          font-size: 0.95rem;
        }

        .how-it-works-section {
          padding: 6rem 2rem;
          max-width: 1200px;
          margin: 0 auto;
        }

        .steps-container {
          display: flex;
          justify-content: center;
          align-items: center;
          gap: 2rem;
          flex-wrap: wrap;
        }

        .step {
          flex: 1;
          min-width: 250px;
          max-width: 300px;
          text-align: center;
          padding: 2rem;
        }

        .step-number {
          width: 80px;
          height: 80px;
          background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
          color: white;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 2rem;
          font-weight: 800;
          margin: 0 auto 1.5rem;
          box-shadow: 0 8px 24px rgba(14, 165, 233, 0.3);
        }

        .step h3 {
          font-size: 1.3rem;
          font-weight: 700;
          color: #0f172a;
          margin-bottom: 0.75rem;
        }

        .step p {
          color: #64748b;
          line-height: 1.6;
        }

        .step-arrow {
          font-size: 2rem;
          color: #0ea5e9;
          font-weight: 300;
        }

        .cta-section {
          padding: 6rem 2rem;
          background: linear-gradient(135deg, #0284c7 0%, #0ea5e9 100%);
        }

        .cta-content {
          max-width: 800px;
          margin: 0 auto;
          text-align: center;
        }

        .cta-content h2 {
          font-size: 3rem;
          font-weight: 800;
          color: white;
          margin-bottom: 1rem;
        }

        .cta-content p {
          font-size: 1.3rem;
          color: rgba(255, 255, 255, 0.9);
          margin-bottom: 2.5rem;
        }

        .cta-content .btn-primary {
          background: white;
          color: #0284c7;
        }

        .cta-content .btn-primary:hover {
          background: #f0f9ff;
        }

        @media (max-width: 768px) {
          .hero-content {
            grid-template-columns: 1fr;
            gap: 3rem;
          }

          .hero-text h1 {
            font-size: 3rem;
          }

          .section-header h2 {
            font-size: 2rem;
          }

          .cta-content h2 {
            font-size: 2rem;
          }

          .step-arrow {
            display: none;
          }
        }
      `}</style>
    </div>
  );
}

export default Landing;