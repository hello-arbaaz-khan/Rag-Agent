import { AlertCircle, CheckCircle2, Info, X } from "lucide-react";
import { useAppContext } from "../../context/AppContext";

const icons = {
  success: CheckCircle2,
  error: AlertCircle,
  info: Info
};

const toneClasses = {
  success: "border-emerald-500/30 bg-emerald-950/90 text-emerald-100",
  error: "border-red-500/30 bg-red-950/90 text-red-100",
  info: "border-blue-500/30 bg-blue-950/90 text-blue-100"
};

const Toast = () => {
  const { toasts, dispatch } = useAppContext();

  return (
    <div className="fixed right-4 top-4 z-50 flex w-[calc(100%-2rem)] max-w-sm flex-col gap-3">
      {toasts.map((toast) => {
        const Icon = icons[toast.type] || Info;
        return (
          <div
            key={toast.id}
            className={`animate-fade-in flex items-start gap-3 rounded-xl border p-4 shadow-soft backdrop-blur ${toneClasses[toast.type] || toneClasses.info}`}
          >
            <Icon className="mt-0.5 h-5 w-5 shrink-0" />
            <p className="min-w-0 flex-1 text-sm font-medium">{toast.message}</p>
            <button
              type="button"
              onClick={() => dispatch({ type: "REMOVE_TOAST", payload: toast.id })}
              className="rounded-lg p-1 transition hover:bg-white/10"
              aria-label="Dismiss notification"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        );
      })}
    </div>
  );
};

export default Toast;
