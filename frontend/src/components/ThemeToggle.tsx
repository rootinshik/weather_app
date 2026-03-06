import { Sun, Moon } from 'lucide-react';
import { useState, useEffect } from 'react';

export function ThemeToggle() {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  useEffect(() => {
    const currentTheme = document.documentElement.getAttribute('data-theme') as 'light' | 'dark' || 'light';
    setTheme(currentTheme);
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    
    // Update state
    setTheme(newTheme);
    
    // Update HTML attribute
    document.documentElement.setAttribute('data-theme', newTheme);
    
    // Update body class
    document.body.className = newTheme;
    
    // Save to localStorage
    localStorage.setItem('theme', newTheme);
    
    // Force CSS variable update
    document.documentElement.style.setProperty('--theme', newTheme);
    
    // Force repaint
    window.dispatchEvent(new Event('themechange'));
  };

  return (
    <button
      onClick={toggleTheme}
      className="flex items-center justify-center w-10 h-10 rounded-xl glass hover:scale-110 transition-all duration-300"
      aria-label={`Сменить тему на ${theme === 'light' ? 'тёмную' : 'светлую'}`}
      title={`Тема: ${theme === 'light' ? 'Светлая' : 'Тёмная'}`}
    >
      {theme === 'light' ? (
        <>
          <Moon className="w-5 h-5 text-gray-700" />
          <span className="sr-only">Переключить на тёмную тему</span>
        </>
      ) : (
        <>
          <Sun className="w-5 h-5 text-yellow-300" />
          <span className="sr-only">Переключить на светлую тему</span>
        </>
      )}
    </button>
  );
}