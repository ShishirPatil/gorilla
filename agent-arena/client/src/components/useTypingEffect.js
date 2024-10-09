import { useState, useEffect } from 'react';

const useTypingEffect = (texts, typingSpeed = 50, pauseDuration = 800) => {
  const [displayedText, setDisplayedText] = useState('');
  const [currentTextIndex, setCurrentTextIndex] = useState(0);
  const [isTyping, setIsTyping] = useState(true);

  useEffect(() => {
    let timeout;
    if (isTyping) {
      if (displayedText.length < texts[currentTextIndex].length) {
        timeout = setTimeout(() => {
          setDisplayedText(texts[currentTextIndex].substring(0, displayedText.length + 1));
        }, typingSpeed);
      } else {
        timeout = setTimeout(() => {
          setIsTyping(false);
        }, pauseDuration);
      }
    } else {
      timeout = setTimeout(() => {
        setDisplayedText('');
        setCurrentTextIndex((prevIndex) => (prevIndex + 1) % texts.length);
        setIsTyping(true);
      }, pauseDuration);
    }
    return () => clearTimeout(timeout);
  }, [displayedText, isTyping, texts, typingSpeed, pauseDuration, currentTextIndex]);

  return displayedText;
};

export default useTypingEffect;
