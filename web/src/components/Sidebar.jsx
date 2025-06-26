import React from 'react';
import '../styles/Sidebar.css';

export default function Sidebar({ onClose, children }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
      </div>
      <div className="sidebar-content">
        {children}
      </div>
    </aside>
  );
}