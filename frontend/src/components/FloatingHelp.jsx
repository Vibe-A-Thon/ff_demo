import React from "react";
import { Button } from "./ui/button";
import { Info } from "lucide-react";

const FloatingHelp = ({ onOpen }) => {
  return (
    <div className="fixed bottom-6 right-6 z-40">
      <Button
        variant="default"
        size="icon"
        onClick={onOpen}
        className="rounded-full shadow-lg"
        data-testid="floating-help-btn"
      >
        <Info className="h-4 w-4" />
      </Button>
    </div>
  );
};

export default FloatingHelp;
