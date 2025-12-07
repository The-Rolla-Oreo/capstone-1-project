import Navbar from "./Navbar/Navbar.jsx";
import Footer from "./Footer/Footer.jsx";
import "./Layout.css";

export default function Layout({ children, isAuthenticated }) {
  return (
    <>
      <Navbar isAuthenticated={isAuthenticated} />

      <main className="layout-main">
        {children}
      </main>

      <Footer />
    </>
  );
}
