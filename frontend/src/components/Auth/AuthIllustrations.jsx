import { FileText, Image as ImageIcon, Lock, MessageSquare, Shield, ShieldCheck, Sparkles } from "lucide-react";

// Floating "document + chat" scene used on the sign-in / sign-up hero panels.
export const DocumentsIllustration = () => (
  <div className="relative mx-auto h-56 w-56">
    <div className="absolute inset-6 rounded-[28px] bg-white/[0.06] backdrop-blur-sm" />

    <div className="absolute left-6 top-8 flex h-16 w-12 -rotate-6 items-center justify-center rounded-lg bg-white/10 shadow-lg">
      <FileText className="h-5 w-5 text-blue-200/80" />
    </div>
    <div className="absolute right-5 top-4 flex h-14 w-11 rotate-6 items-center justify-center rounded-lg bg-white/10 shadow-lg">
      <ImageIcon className="h-4 w-4 text-indigo-200/80" />
    </div>
    <div className="absolute bottom-8 left-8 flex h-14 w-11 rotate-3 items-center justify-center rounded-lg bg-white/10 shadow-lg">
      <FileText className="h-4 w-4 text-blue-200/80" />
    </div>
    <div className="absolute bottom-4 right-9 flex h-14 w-11 -rotate-3 items-center justify-center rounded-lg bg-white/10 shadow-lg">
      <FileText className="h-4 w-4 text-indigo-200/80" />
    </div>

    <div className="absolute left-1/2 top-1/2 flex w-32 -translate-x-1/2 -translate-y-1/2 flex-col gap-1.5 rounded-xl bg-white/95 p-3 shadow-xl">
      <div className="h-2 w-16 rounded-full bg-slate-300" />
      <div className="h-2 w-20 rounded-full bg-slate-200" />
      <div className="h-2 w-12 rounded-full bg-slate-200" />
    </div>

    <div className="absolute -right-1 top-1/2 flex h-11 w-11 -translate-y-1/2 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 shadow-lg shadow-blue-950/40">
      <MessageSquare className="h-5 w-5 text-white" />
    </div>
    <div className="absolute -left-2 -top-2 flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-indigo-400 to-blue-500 shadow-lg">
      <Sparkles className="h-4 w-4 text-white" />
    </div>
  </div>
);

// Central shield/lock scene used on password screens (forgot / reset / change).
export const ShieldIllustration = ({ variant = "shield" }) => (
  <div className="relative mx-auto flex h-56 w-56 items-center justify-center">
    <div className="absolute h-44 w-44 rounded-full bg-blue-500/10" />
    <div className="absolute h-32 w-32 rounded-full bg-blue-500/10" />

    <div className="relative flex h-24 w-24 items-center justify-center rounded-3xl bg-gradient-to-br from-blue-500 to-indigo-600 shadow-xl shadow-blue-950/40">
      {variant === "lock" ? <Lock className="h-11 w-11 text-white" /> : <Shield className="h-11 w-11 text-white" />}
    </div>

    <div className="absolute left-3 top-6 flex h-9 w-9 items-center justify-center rounded-full bg-white/10 shadow-lg">
      <Lock className="h-4 w-4 text-blue-100" />
    </div>
    <div className="absolute right-2 top-10 flex h-8 w-8 items-center justify-center rounded-full bg-white/10 shadow-lg">
      <ShieldCheck className="h-4 w-4 text-indigo-100" />
    </div>
    <div className="absolute bottom-6 right-6 flex h-9 w-9 items-center justify-center rounded-full bg-white/10 shadow-lg">
      <Shield className="h-4 w-4 text-blue-100" />
    </div>
  </div>
);