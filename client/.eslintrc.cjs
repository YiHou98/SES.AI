module.exports = {
  // Define the environments your code runs in
  env: {
    browser: true,
    es2021: true,
    node: true,
  },
  
  // Start with recommended rule sets from ESLint and the React plugin
  extends: [
    'eslint:recommended',
    'plugin:react/recommended',
    'plugin:react/jsx-runtime' // Add this for modern React (no need to import React)
  ],
  
  // Specify parser options for modern JavaScript
  parserOptions: {
    ecmaFeatures: {
      jsx: true
    },
    ecmaVersion: 'latest',
    sourceType: 'module',
  },
  
  // Add the React plugin
  plugins: [
    'react'
  ],
  
  // Define your custom rules here
  rules: {
    // You can turn off the prop-types rule if you find it too noisy
    'react/prop-types': 'off', 
  },
  
  // Tell the React plugin to automatically detect your React version
  settings: {
    react: {
      version: 'detect',
    },
  },
};