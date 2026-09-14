import React, { useEffect } from "react";
import { Link } from "react-router-dom";
import { User, Menu, Moon, Sun } from "lucide-react";
import { Button } from "../ui/button";

interface TopNavProps {
  onMenuClick?: () => void;
}

export function TopNav({ onMenuClick }: TopNavProps) {
  const [isDark, setIsDark] = React.useState(false);

  useEffect(() => {
    // Check local storage or system preference on mount
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "dark" || (!savedTheme && window.matchMedia("(prefers-color-scheme: dark)").matches)) {
      setIsDark(true);
      document.documentElement.classList.add('dark');
    }
  }, []);

  const toggleTheme = () => {
    const newTheme = !isDark;
    setIsDark(newTheme);
    if (newTheme) {
      document.documentElement.classList.add('dark');
      localStorage.setItem("theme", "dark");
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem("theme", "light");
    }
  };

  return (
    <header className="flex h-14 items-center gap-4 border-b border-gray-200 bg-white px-4 lg:h-[60px] dark:border-gray-800 dark:bg-gray-950 transition-colors duration-200 z-10 sticky top-0">
      <Button variant="ghost" size="icon" className="lg:hidden" onClick={onMenuClick}>
        <Menu className="h-5 w-5" />
        <span className="sr-only">Toggle navigation menu</span>
      </Button>
      
      <div className="w-full flex-1">
        {/* Search or breadcrumbs could go here */}
      </div>

      <Button variant="ghost" size="icon" onClick={toggleTheme} aria-label="Toggle theme">
        {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
      </Button>
      
      <Link to="/profile">
        <Button variant="ghost" size="icon" className="rounded-full" aria-label="User profile">
          <User className="h-5 w-5" />
        </Button>
      </Link>
    </header>
  );
}
