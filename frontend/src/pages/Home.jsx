import { Link } from 'react-router-dom'
import { ShieldCheck, Zap, RefreshCw, AlertTriangle } from 'lucide-react'

export default function Home() {
  return (
    <div className="max-w-6xl mx-auto px-4 py-12">
      {/* Hero */}
      <div className="text-center mb-16">
        <div className="inline-flex items-center gap-2 bg-green-50 text-green-700 px-4 py-2 rounded-full text-sm font-medium mb-6">
          <span>🤖</span>
          <span>Powered by AUREV AI — Intelligent Payment Recovery</span>
        </div>
        <h1 className="text-5xl font-bold text-gray-900 mb-4">
          Fresh groceries,
          <span className="text-green-500"> delivered.</span>
        </h1>
        <p className="text-xl text-gray-500 mb-8 max-w-2xl mx-auto">
          NIVORA uses AUREV AI to ensure every payment is handled safely — even when things go wrong.
        </p>
        <Link to="/products" className="btn-primary text-lg px-8 py-4 inline-block">
          Start Shopping →
        </Link>
      </div>

      {/* Features */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
        {[
          { icon: ShieldCheck, title: 'Safe Payments', desc: 'No duplicate charges. Ever.', color: 'text-green-500' },
          { icon: Zap, title: 'AUREV AI Recovery', desc: 'Automatic failure recovery in seconds.', color: 'text-blue-500' },
          { icon: RefreshCw, title: 'Smart Retry', desc: 'Retries only when safe to do so.', color: 'text-purple-500' },
          { icon: AlertTriangle, title: 'Zero Risk Escalation', desc: 'Unknown states are always escalated.', color: 'text-orange-500' },
        ].map(({ icon: Icon, title, desc, color }) => (
          <div key={title} className="card text-center">
            <div className={`${color} mb-3 flex justify-center`}><Icon size={32} /></div>
            <h3 className="font-semibold text-gray-900 mb-1">{title}</h3>
            <p className="text-gray-500 text-sm">{desc}</p>
          </div>
        ))}
      </div>

      {/* AUREV CTA */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 rounded-3xl p-8 text-white text-center">
        <h2 className="text-2xl font-bold mb-2">Watch AUREV AI in action</h2>
        <p className="text-blue-200 mb-6">See live payment recovery, ML classification, and real-time decisions.</p>
        <Link to="/aurev" className="bg-white text-blue-600 font-semibold px-8 py-3 rounded-xl hover:bg-blue-50 transition-colors inline-block">
          Open AUREV Dashboard
        </Link>
      </div>
    </div>
  )
}
