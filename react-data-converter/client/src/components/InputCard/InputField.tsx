import React from 'react';

// InputField.tsx
interface InputFieldProps {
  label: string;
  id: string;
  type: string;
  value: string;
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
}

const InputField: React.FC<InputFieldProps> = ({ label, id, type = 'text', value, onChange }) => {
  return (
    <div className="form-group">
      <label htmlFor={id}>{label}:</label>
      <input
        type={type}
        className="form-control"
        id={id}
        value={value}
        onChange={onChange} />
    </div>
  );
};

export default React.memo(InputField);
