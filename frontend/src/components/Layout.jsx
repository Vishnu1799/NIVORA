import { Outlet, Link, useNavigate } from 'react-router-dom'
import { ShoppingCart, User, LogOut, LayoutDashboard, Activity } from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import { useCartStore } from '../store/cartStore'

export default function Layout() {
  const { user, isAuthenticated, logout } = useAuthStore()
  const items = useCartStore(s => s.items)
  const navigate = useNavigate()
  const cartCount = items.reduce((s, i) => s + i.quantity, 0)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-100 sticky top-0 z-50 shadow-sm">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <span className="text-2xl">🥦</span>
            <span className="font-bold text-xl text-green-600">NIVORA</span>
          </Link>

          <div className="flex items-center gap-2">
            <Link to="/products" className="px-4 py-2 text-gray-600 hover:text-green-600 font-medium transition-colors">
              Shop
            </Link>
            <Link to="/aurev" className="px-4 py-2 text-blue-600 hover:text-blue-700 font-medium transition-colors flex items-center gap-1">
              <Activity size={16} />
              AUREV AI
            </Link>
            {user?.role === 'MERCHANT' && (
              <Link to="/merchant" className="px-4 py-2 text-gray-600 hover:text-green-600 font-medium transition-colors">
                Dashboard
              </Link>
            )}
            <Link to="/cart" className="relative p-2 text-gray-600 hover:text-green-600 transition-colors">
              <ShoppingCart size={22} />
              {cartCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-green-500 text-white text-xs w-5 h-5 rounded-full flex items-center justify-center font-bold">
                  {cartCount}
                </span>
              )}
            </Link>
            {isAuthenticated ? (
              <div className="flex items-center gap-2">
                <Link to="/orders" className="flex items-center gap-1 px-3 py-2 text-gray-600 hover:text-green-600 text-sm">
                  <User size={16} />
                  {user?.name?.split(' ')[0]}
                </Link>
                <button onClick={handleLogout} className="p-2 text-gray-400 hover:text-red-500 transition-colors">
                  <LogOut size={18} />
                </button>
              </div>
            ) : (
              <Link to="/login" className="btn-primary py-2 px-4 text-sm">
                Sign in
              </Link>
            )}
          </div>
        </div>
      </nav>
      <main>
        <Outlet />
      </main>
    </div>
  )
}
