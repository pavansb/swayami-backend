import React from 'react';

const Footer = () => {
  return (
    <footer className="py-16 border-t border-gray-100 bg-white">
      <div className="max-w-6xl mx-auto px-6">
        <div className="flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex items-center">
            <img 
              src="/lovable-uploads/9cf37de0-ba28-4f72-9b5c-2c838d6562f4.png" 
              alt="Swayami" 
              className="h-12 w-auto mb-4"
            />
          </div>
          
          <div className="flex items-center gap-8">
            <a href="#" className="text-sm text-[#4A4A4A] hover:text-[#1A1A1A] transition-colors">
              Terms
            </a>
            <a href="#" className="text-sm text-[#4A4A4A] hover:text-[#1A1A1A] transition-colors">
              Privacy
            </a>
            <a href="#" className="text-sm text-[#4A4A4A] hover:text-[#1A1A1A] transition-colors">
              Contact
            </a>
            <div className="flex items-center gap-4">
              <a href="#" className="text-[#4A4A4A] hover:text-[#1A1A1A] transition-colors">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0C5.374 0 0 5.373 0 12 0 17.302 3.438 21.8 8.207 23.387c.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z"/>
                </svg>
              </a>
              <a href="#" className="text-[#4A4A4A] hover:text-[#1A1A1A] transition-colors">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </a>
            </div>
          </div>
        </div>
        
        <div className="text-center text-sm text-[#4A4A4A]/70 mt-12">
          Swayami — the discipline to become who you truly are.
        </div>
      </div>
    </footer>
  );
};

export default Footer;
