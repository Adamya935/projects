import java.util.ArrayList;
import java.util.List;
import java.util.Map;

class IRGenerator {
    private List<Token> tokens;
    private Map<String, Semantic.SymbolInfo> symbolTable;
    private List<String> instructions = new ArrayList<>();
    private int tempCount = 0;
    private int pos = 0;

    IRGenerator(List<Token> tokens, Map<String, Semantic.SymbolInfo> symbolTable) {
        this.tokens      = tokens;
        this.symbolTable = symbolTable;
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

    // Generate a new temp variable: t0, t1, t2 ...
    private String newTemp() {
        return "t" + tempCount++;
    }

    // ─────────────────────────────────────────────────────────────────
    // Generate IR for declaration: int a = 10;  or  int a;
    // ─────────────────────────────────────────────────────────────────
    private void generateDeclaration() {
        Token keyword    = advance();   // KEYWORD  e.g. int
        Token identifier = advance();   // IDENTIFIER e.g. a
        String varName   = identifier.value;
        String varType   = keyword.value;

        if (hasMore() && peek().value.equals("=")) {
            advance(); // consume '='
            Token rhs = advance(); // NUMBER
            advance(); // consume ';'

            // TAC: t0 = 10
            //      a  = t0
            String temp = newTemp();
            instructions.add(temp + " = " + rhs.value);
            instructions.add(varName + " = " + temp);

        } else {
            advance(); // consume ';'

            // TAC: a = null  (declared but not initialized)
            instructions.add(varName + " = null");
        }
    }

    // ─────────────────────────────────────────────────────────────────
    // Generate IR for assignment: a = 20;
    // ─────────────────────────────────────────────────────────────────
    private void generateAssignment() {
        Token identifier = advance();   // IDENTIFIER
        String varName   = identifier.value;

        advance(); // consume '='

        Token rhs = advance(); // NUMBER
        advance(); // consume ';'

        // TAC: t1 = 20
        //      a  = t1
        String temp = newTemp();
        instructions.add(temp + " = " + rhs.value);
        instructions.add(varName + " = " + temp);
    }

    // ─────────────────────────────────────────────────────────────────
    // Main entry point
    // ─────────────────────────────────────────────────────────────────
    public List<String> generate() {
        System.out.println("\n--- IR Generation (Three Address Code) ---");

        while (hasMore()) {
            Token t = peek();

            if (t.type.equals("KEYWORD")) {
                generateDeclaration();
            } else if (t.type.equals("IDENTIFIER")) {
                generateAssignment();
            } else {
                throw new RuntimeException(
                    "IR Error: Unexpected token -> " + t
                );
            }
        }

        printIR();
        return instructions;
    }

    // ─────────────────────────────────────────────────────────────────
    // Print generated IR instructions
    // ─────────────────────────────────────────────────────────────────
    private void printIR() {
        System.out.println();
        System.out.println("+-------+----------------------+");
        System.out.println("| Line  | Instruction          |");
        System.out.println("+-------+----------------------+");

        for (int i = 0; i < instructions.size(); i++) {
            System.out.printf("| %-5d | %-20s |%n", i + 1, instructions.get(i));
        }

        System.out.println("+-------+----------------------+");
        System.out.println("\nIR Generation: Complete ");
    }
}