import './style.css';
export const metadata = { title: 'DriveOS', description: 'You drive. It handles everything around the drive.' };
export default function Layout({ children }) {
  return <html lang="en"><body>{children}</body></html>;
}
