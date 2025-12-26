import React from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { IconDefinition } from '@fortawesome/fontawesome-svg-core';

interface IconButtonProps {
  icon: IconDefinition;
  onClick: () => void;
  ariaLabel: string;
  className?: string;
}

const IconButton: React.FC<IconButtonProps> = React.memo(({
  icon,
  onClick,
  ariaLabel,
  className = ''
}) => (
  <button
    type="button"
    className={`btn ${className}`}
    aria-label={ariaLabel}
    onClick={onClick}
  >
    <FontAwesomeIcon icon={icon} />
  </button>
));

IconButton.displayName = 'IconButton';
export default IconButton;
