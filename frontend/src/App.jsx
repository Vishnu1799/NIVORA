import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import Home from './pages/Home'
import Login from './pages/Login'
import Register from './pages/Register'
import Products from './pages/Products'
import Cart from './pages/Cart'
import Checkout from './pages/Checkout'
import PaymentProcessing from './pages/PaymentProcessing'
import PaymentResult from './pages/PaymentResult'
import Orders from './pages/Orders'
import MerchantDashboard from './pages/MerchantDashboard'
import AurevDashboard from './pages/AurevDashboard'
import Layout from './components/Layout'

function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuthStore()
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="products" element={<Products />} />
          <Route path="cart" element={<Cart />} />
          <Route path="checkout" element={<ProtectedRoute><Checkout /></ProtectedRoute>} />
          <Route path="payment/:transactionId" element={<ProtectedRoute><PaymentProcessing /></ProtectedRoute>} />
          <Route path="payment-result/:transactionId" element={<ProtectedRoute><PaymentResult /></ProtectedRoute>} />
          <Route path="orders" element={<ProtectedRoute><Orders /></ProtectedRoute>} />
          <Route path="merchant" element={<ProtectedRoute><MerchantDashboard /></ProtectedRoute>} />
          <Route path="aurev" element={<AurevDashboard />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
