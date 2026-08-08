// Hidden feature flags — NOT in the flag management system
export const HIDDEN_FLAGS = {
  ENABLE_EXPERIMENTAL_CHECKOUT: process.env.REACT_APP_EXP_CHECKOUT === 'true',
  ENABLE_AI_RECOMMENDATIONS: true, // Hardcoded, should be managed
  DARK_MODE_BETA: false,
};
