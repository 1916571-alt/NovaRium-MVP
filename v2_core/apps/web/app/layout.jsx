import "./globals.css";
import NavBar from "@/components/NavBar";

export const metadata = {
  title: "NovaRium V2 Web",
  description: "Experiment + SQL learning platform"
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <NavBar />
        <main className="container">{children}</main>
      </body>
    </html>
  );
}

