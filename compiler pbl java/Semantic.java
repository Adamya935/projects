import java.util.HashMap;
import java.util.List;
import java.util.Map;

class Semantic {
    private List<Token> tokens;
    private int pos = 0;

    // ── Symbol Table ─────────────────────────────────────────────────
    // Rule 5: Every declaration/assignment reflects in symbol table
    private Map<String, SymbolInfo> symbolTable = new HashMap<>();

    static class SymbolInfo {
        String type;
        String value;
        boolean isInitialized;

        SymbolInfo(String type, String value, boolean isInitialized) {
            this.type          = type;
            this.value         = value;
            this.isInitialized = isInitialized;
        }
    }
    // ─────────────────────────────────────────────────────────────────

    Semantic(List<Token> tokens) {
        this.tokens = tokens;
    }

    public Map<String, SymbolInfo> getSymbolTable() {
        return symbolTable;
    }

    private Token peek() {
        if (pos >= tokens.size()) return null;
        return tokens.get(pos);
    }

    private Token advance() {
        return tokens.get(pos++);
    }

    private boolean hasMore() {
        return pos < tokens.size();
    }

    // ─────────────────────────────────────────────────────────────────
    // RULE 1: Declaration Check
    // Variable declared with keyword → added to symbol table
    // ─────────────────────────────────────────────────────────────────
    private void checkDeclaration() {
        Token keyword    = advance();   // e.g. int
        Token identifier = advance();   // e.g. a
        String varName   = identifier.value;
        String varType   = keyword.value;

        // RULE 2: Duplicate Declaration Check
        if (symbolTable.containsKey(varName)) {
            throw new RuntimeException(
                "Semantic Error [Rule 2]: Variable '" + varName + "' already declared"
            );
        }

        // int a = 10;
        if (hasMore() && peek().value.equals("=")) {
            advance(); // consume '='
            Token rhs = advance(); // value after '='

            // RULE 4: Type Mismatch Check
            // RHS must be NUMBER for numeric types
            if (!rhs.type.equals("NUMBER")) {
                throw new RuntimeException(
                    "Semantic Error [Rule 4]: Type mismatch — cannot assign " +
                    rhs.type + "(" + rhs.value + ")" + " to " + varType + " variable '" + varName + "'"
                );
            }

            advance(); // consume ';'

            // RULE 5: Symbol Table Update — declared + initialized
            symbolTable.put(varName, new SymbolInfo(varType, rhs.value, true));
            System.out.println("Rule 1 Passed: '" + varName + "' declared as " + varType);
            System.out.println("Rule 4 Passed: Type check passed for '" + varName + "'");
            System.out.println("Rule 5 Passed: Symbol table updated → " + varName +
                               " = { type: " + varType + ", value: " + rhs.value + ", initialized: true }");

        } else {
            // int a;
            advance(); // consume ';'

            // RULE 5: Symbol Table Update — declared, not initialized
            symbolTable.put(varName, new SymbolInfo(varType, null, false));
            System.out.println("Rule 1 Passed: '" + varName + "' declared as " + varType);
            System.out.println("Rule 5 Passed: Symbol table updated → " + varName +
                               " = { type: " + varType + ", value: null, initialized: false }");
        }
    }

    // ─────────────────────────────────────────────────────────────────
    // RULE 3: Use Before Declaration Check
    // Assignment only allowed if variable already in symbol table
    // ─────────────────────────────────────────────────────────────────
    private void checkAssignment() {
        Token identifier = advance();   // e.g. a
        String varName   = identifier.value;

        // RULE 3: must be declared first
        if (!symbolTable.containsKey(varName)) {
            throw new RuntimeException(
                "Semantic Error [Rule 3]: Variable '" + varName + "' used before declaration"
            );
        }

        advance(); // consume '='

        Token rhs          = advance(); // value after '='
        String declaredType = symbolTable.get(varName).type;

        // RULE 4: Type Mismatch Check
        if (!rhs.type.equals("NUMBER")) {
            throw new RuntimeException(
                "Semantic Error [Rule 4]: Type mismatch — cannot assign " +
                rhs.type + "(" + rhs.value + ")" + " to " + declaredType + " variable '" + varName + "'"
            );
        }

        advance(); // consume ';'

        // RULE 5: Symbol Table Update — update value + mark initialized
        symbolTable.get(varName).value         = rhs.value;
        symbolTable.get(varName).isInitialized = true;

        System.out.println("Rule 3 Passed: '" + varName + "' was declared before use");
        System.out.println("Rule 4 Passed: Type check passed for '" + varName + "'");
        System.out.println("Rule 5 Passed: Symbol table updated → " + varName +
                           " = { type: " + declaredType + ", value: " + rhs.value + ", initialized: true }");
    }

    // ─────────────────────────────────────────────────────────────────
    // Main entry point (American spelling for WebServer compatibility)
    // ─────────────────────────────────────────────────────────────────
    public void analyze() {
        analyse();
    }

    // ─────────────────────────────────────────────────────────────────
    // Main entry point
    // ─────────────────────────────────────────────────────────────────
    public void analyse() {
        System.out.println("\n--- Semantic Analysis ---");

        while (hasMore()) {
            Token t = peek();

            if (t.type.equals("KEYWORD")) {
                checkDeclaration();   // handles Rule 1, 2, 4, 5
            } else if (t.type.equals("IDENTIFIER")) {
                checkAssignment();    // handles Rule 3, 4, 5
            } else {
                throw new RuntimeException(
                    "Semantic Error: Unexpected token -> " + t
                );
            }
        }

        System.out.println("\nSemantic Analysis: Passed ✓");
        printSymbolTable();
    }

    // ─────────────────────────────────────────────────────────────────
    // Symbol Table Display
    // ─────────────────────────────────────────────────────────────────
    private void printSymbolTable() {
        System.out.println("\nSymbol Table:");
        System.out.println("+------------+--------+---------+-------------+");
        System.out.println("| Variable   |  Type  |  Value  | Initialized |");
        System.out.println("+------------+--------+---------+-------------+");

        for (Map.Entry<String, SymbolInfo> entry : symbolTable.entrySet()) {
            String     name = entry.getKey();
            SymbolInfo s    = entry.getValue();
            System.out.printf("| %-10s | %-6s | %-7s | %-11s |%n",
                name,
                s.type,
                s.value == null ? "null" : s.value,
                s.isInitialized
            );
        }

        System.out.println("+------------+--------+---------+-------------+");
    }
}