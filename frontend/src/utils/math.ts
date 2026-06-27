/**
 * 将简单 LaTeX 数学表达式转换为 Unicode 文本
 * 处理 AI 输出中残留的 $...$ 格式
 */

const LATEX_MAP: Record<string, string> = {
  '\\geq': '≥', '\\leq': '≤', '\\neq': '≠',
  '\\times': '×', '\\div': '÷', '\\pm': '±',
  '\\sqrt': '√', '\\pi': 'π', '\\infty': '∞',
  '\\alpha': 'α', '\\beta': 'β', '\\gamma': 'γ',
  '\\angle': '∠', '\\degree': '°',
  '\\approx': '≈', '\\equiv': '≡',
  '\\rightarrow': '→', '\\leftarrow': '←',
  '\\Rightarrow': '⇒',
  '\\quad': ' ', '\\qquad': '  ',
  '\\text{': '', '\\mathrm{': '',
  '\\left': '', '\\right': '',
  '\\(': '', '\\)': '', '\\[': '', '\\]': '',
}

// 上标映射
const SUPERSCRIPT: Record<string, string> = {
  '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
  '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
  'n': 'ⁿ', 'i': 'ⁱ', '+': '⁺', '-': '⁻', '(': '⁽', ')': '⁾',
}

// 下标映射
const SUBSCRIPT: Record<string, string> = {
  '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄',
  '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉',
  'a': 'ₐ', 'e': 'ₑ', 'i': 'ᵢ', 'j': 'ⱼ',
  'n': 'ₙ', 'x': 'ₓ',
}

export function latexToText(text: string): string {
  if (!text) return text

  let result = text

  // 替换 \frac{a}{b} → a/b
  result = result.replace(/\\frac\{([^}]*)\}\{([^}]*)\}/g, '$1/$2')

  // 替换 \sqrt{x} → √(x)
  result = result.replace(/\\sqrt\{([^}]*)\}/g, '√($1)')

  // 替换 x^{n} → xⁿ
  result = result.replace(/\^{([^}]*)}/g, (_, content) =>
    content.split('').map((c: string) => SUPERSCRIPT[c] || c).join('')
  )
  // 替换 x^n → xⁿ（单字符）
  result = result.replace(/\^([0-9n])/g, (_, c) => SUPERSCRIPT[c] || c)

  // 替换 x_{n} → xₙ
  result = result.replace(/_{([^}]*)}/g, (_, content) =>
    content.split('').map((c: string) => SUBSCRIPT[c] || c).join('')
  )
  // 替换 x_n → xₙ（单字符）
  result = result.replace(/_([0-9nx])/g, (_, c) => SUBSCRIPT[c] || c)

  // 替换 LaTeX 命令
  for (const [cmd, replacement] of Object.entries(LATEX_MAP)) {
    result = result.replace(new RegExp(cmd.replace(/\\/g, '\\\\'), 'g'), replacement)
  }

  // 移除残留的花括号
  result = result.replace(/\{([^{}]*)\}/g, '$1')

  // 移除 $ 包裹
  result = result.replace(/\$\$(.*?)\$\$/g, '$1')
  result = result.replace(/\$(.*?)\$/g, '$1')

  // 清理多余空格
  result = result.replace(/\s{2,}/g, ' ').trim()

  return result
}
