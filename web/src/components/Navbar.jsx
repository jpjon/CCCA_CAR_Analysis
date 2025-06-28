import React from 'react';
import '../styles/Navbar.css';
import { FaGithub } from 'react-icons/fa';
import { FaBars } from 'react-icons/fa';

export default function Navbar({ onToggleSidebar, githubUrl = "#" }) {
  return (
    <nav className="navbar">
      <div className="navbar-left">
        <button className="sidebar-toggle" onClick={onToggleSidebar}>
          <FaBars size={20} />
        </button>
        <div className="brand-logo">
          <div className="brand-line">CENTER FOR</div>
          <div className="brand-line brand-main">CLIMATE CRIME</div>
          <div className="brand-line brand-main">ANALYSIS</div>
        </div>
      </div>
      <div className="navbar-right">
        <a href={githubUrl} target="_blank" rel="noopener noreferrer" className="github-link">
          <FaGithub size={24} />
        </a>
      </div>
    </nav>
  );
}