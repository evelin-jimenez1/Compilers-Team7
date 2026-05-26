class AssemblerGenerator:
    def __init__(self):
        self.asm_code = []
        self.data_section = [".section .data", "    # Variables globales aquí"]
        self.text_section = [".section .text", ".global main", "main:"]

    def generate(self, tac_instructions):
        """
        Toma la lista de TAC y genera el archivo ensamblador.
        """
        for instr in tac_instructions:
            self._translate(instr)
        
        # Unir todo el código generado
        full_code = self.data_section + self.text_section
        return "\n".join(full_code)

    def _translate(self, instr):
        # Limpieza básica
        parts = instr.replace(':', '').split()
        
        # Mapeo de instrucciones (TAC a ASM x86)
        # 1. Asignaciones con operación aritmética: t1 = a + b
        if len(parts) >= 5 and parts[3] == '+':
            self.text_section.append(f"    mov eax, {parts[2]}")
            self.text_section.append(f"    add eax, {parts[4]}")
            self.text_section.append(f"    mov {parts[0]}, eax")
            
        # 2. Asignaciones directas: t1 = a
        elif len(parts) >= 3 and parts[1] == '=':
            self.text_section.append(f"    mov eax, {parts[2]}")
            self.text_section.append(f"    mov {parts[0]}, eax")
            
        # 3. Etiquetas (Labels)
        elif instr.startswith("Label"):
            self.text_section.append(f"{parts[1]}:")
            
        # 4. Saltos condicionales: ifFalse t1 goto L1
        elif 'ifFalse' in parts:
            self.text_section.append(f"    cmp {parts[1]}, 0")
            self.text_section.append(f"    je {parts[3]}")
            
        # 5. Saltos incondicionales: goto L1
        elif 'goto' in parts:
            self.text_section.append(f"    jmp {parts[1]}")

        # 6. Retorno: return a
        elif 'return' in parts:
            val = parts[1] if len(parts) > 1 else "0"
            self.text_section.append(f"    mov eax, {val}")
            self.text_section.append("    ret")