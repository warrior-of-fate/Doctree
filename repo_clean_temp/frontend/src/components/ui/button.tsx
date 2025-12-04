import React from 'react';

export const Button = React.forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement> & {
    variant?: 'default' | 'outline' | 'ghost' | 'secondary';
    size?: 'default' | 'sm' | 'lg' | 'icon';
    asChild?: boolean;
  }
>(({ className, variant = 'default', size = 'default', asChild, ...props }, ref) => {
  const baseStyles = 'inline-flex items-center justify-center rounded-md font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed';
  
  const variants = {
    default: 'bg-blue-600 text-white hover:bg-blue-700',
    outline: 'border border-gray-300 bg-white text-gray-900 hover:bg-gray-50',
    ghost: 'hover:bg-gray-100 text-gray-900',
    secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300',
  };

  const sizes = {
    default: 'px-4 py-2 text-sm',
    sm: 'px-2 py-1 text-xs',
    lg: 'px-6 py-3 text-lg',
    icon: 'h-10 w-10 p-0',
  };

  const combinedClassName = `${baseStyles} ${variants[variant]} ${sizes[size]} ${className || ''}`;

  if (asChild) {
    return React.Children.map(props.children as React.ReactNode, (child) =>
      React.isValidElement(child) ? React.cloneElement(child, { className: combinedClassName } as any) : child
    )?.[0];
  }

  return (
    <button ref={ref} className={combinedClassName} {...props} />
  );
});

Button.displayName = 'Button';
