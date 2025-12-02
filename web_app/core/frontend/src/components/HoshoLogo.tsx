import React from 'react';

interface HoshoLogoProps {
  className?: string;
  size?: number;
}

const HoshoLogo: React.FC<HoshoLogoProps> = ({ className = '', size = 40 }) => {
  return (
    <img
      src="/Hosho-Logo.png"
      alt="HOSHŌ DIGITAL Logo"
      width={size}
      height={size}
      className={`${className} object-contain`}
      style={{
        width: size,
        height: size,
        borderRadius: 0,
        imageRendering: 'crisp-edges'
      }}
    />
  );
};

export default HoshoLogo;
