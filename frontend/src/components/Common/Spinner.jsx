const Spinner = ({ className = "h-4 w-4" }) => (
  <span
    className={`${className} inline-block animate-spin rounded-full border-2 border-current border-r-transparent`}
    aria-label="Loading"
  />
);

export default Spinner;
