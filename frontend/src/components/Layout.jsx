import Navbar from './Navbar/Navbar.jsx';
import Footer from './Footer/Footer.jsx';

export default function Layout({ children, isAuthenticated }) {
  return (
    <>
      <Navbar isAuthenticated={isAuthenticated} />
      <main style={{ minHeight: '100vh' }}>
        {children}
      </main>
      <Footer />
    </>
  );
}