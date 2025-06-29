import React from 'react';
import '../styles/Sidebar.css';
import CCCALogo from '../assets/CCCA-Logo.svg';

export default function Sidebar({ onClose, children }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
      </div>
      <div className="sidebar-content">
        <img
          src={CCCALogo}
          alt="CCCA Logo"
          />
        {children}
      </div>
    </aside>
  );
}