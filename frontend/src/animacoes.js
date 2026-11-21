// Animações do Motion num lugar só, para o site inteiro ter o mesmo "ritmo".
// Quem escolheu "Reduzir animações" (ou tem isso ligado no sistema) não vê
// movimento: o <MotionConfig reducedMotion> em App.jsx cuida disso.

export const MOLA = { type: "spring", stiffness: 260, damping: 26 };
export const MOLA_SUAVE = { type: "spring", stiffness: 140, damping: 22 };

// Troca de página: entra subindo, sai esmaecendo
export const pagina = {
  inicial: { opacity: 0, y: 18 },
  visivel: { opacity: 1, y: 0, transition: { duration: 0.35, ease: [0.22, 1, 0.36, 1] } },
  saida: { opacity: 0, y: -10, transition: { duration: 0.18 } },
};

// Grade de cartazes: um depois do outro, em cascata
export const grade = {
  inicial: {},
  visivel: { transition: { staggerChildren: 0.045, delayChildren: 0.05 } },
};

export const itemDaGrade = {
  inicial: { opacity: 0, y: 26, scale: 0.96 },
  visivel: { opacity: 1, y: 0, scale: 1, transition: MOLA },
};

// Blocos de texto que aparecem em sequência
export const sequencia = {
  inicial: {},
  visivel: { transition: { staggerChildren: 0.08 } },
};

export const surgir = {
  inicial: { opacity: 0, y: 14 },
  visivel: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.22, 1, 0.36, 1] } },
};
