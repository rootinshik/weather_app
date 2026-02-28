import { Link } from 'react-router-dom';

export function NotFoundPage() {
  return (
    <div>
      <h1>404 &mdash; Page Not Found</h1>
      <p>The page you are looking for does not exist.</p>
      <Link to="/">Go to home page</Link>
    </div>
  );
}
