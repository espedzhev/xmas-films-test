import { Link, useLocation } from "react-router-dom";

export default function LinkWithQuery({ children, to, ...props }) {
  const { search } = useLocation();
  return (
    <Link to={to + search} {...props}>
      {children}
    </Link>
  );
}
