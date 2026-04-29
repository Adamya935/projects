import java.util.ArrayList;
import java.util.List;

class Syntax {
    private List<Token> tokens;
    private int pos = 0;

    // ── Parse Tree Node ──────────────────────────────────────────────
    static class ParseNode {
        String label;
        List<ParseNode> children = new ArrayList<>();

        ParseNode(String label) {
            this.label = label;
        }

        void addChild(ParseNode child) {
            children.add(child);
        }

        void print(String prefix, boolean isLast) {
            String connector = isLast ? " " : "  ";
            String childPrefix = isLast ? "    " : "   ";

            System.out.println(prefix + connector + label);

            for (int i = 0; i < children.size(); i++) {
                boolean lastChild = (i == children.size() - 1);
                children.get(i).print(prefix + childPrefix, lastChild);
            }
        }
    }
    // ─────────────────────────────────────────────────────────────────

    Syntax(List<Token> tokens) {
        this.tokens = tokens;
    }

    private Token peek() {
        if (pos >= tokens.size()) return null;
        return tokens.get(pos);
    }

    private void advance() {
        pos++;
    }

    private ParseNode match(String type, String value) {
        Token t = peek();

        if (t == null)
            throw new RuntimeException("Unexpected end of input");

        if (!t.type.equals(type))
            throw new RuntimeException("Syntax Error: Expected " + type + " but found " + t);

        if (value != null && !t.value.equals(value))
            throw new RuntimeException("Syntax Error: Expected '" + value + "' but found " + t);

        advance();
        return new ParseNode(t.type + "(" + t.value + ")");
    }

    private ParseNode statement() {
        Token t = peek();
        ParseNode node = new ParseNode("statement");

        if (t.type.equals("KEYWORD")) {
            node.addChild(declaration());
        } else if (t.type.equals("IDENTIFIER")) {
            node.addChild(assignment());
        } else {
            throw new RuntimeException("Syntax Error: Invalid start -> " + t);
        }

        return node;
    }

    private ParseNode declaration() {
        ParseNode node = new ParseNode("declaration");

        node.addChild(match("KEYWORD", null));
        node.addChild(match("IDENTIFIER", null));

        if (peek() != null && peek().value.equals("=")) {
            node.addChild(match("OPERATOR", "="));
            node.addChild(match("NUMBER", null));
        }

        node.addChild(match("DELIMITER", ";"));
        return node;
    }

    private ParseNode assignment() {
        ParseNode node = new ParseNode("assignment");

        node.addChild(match("IDENTIFIER", null));
        node.addChild(match("OPERATOR", "="));
        node.addChild(match("NUMBER", null));
        node.addChild(match("DELIMITER", ";"));

        return node;
    }

    public ParseNode parse() {
        ParseNode tree = statement();
        System.out.println("Syntax is correct");
        System.out.println("\nParse Tree:");
        System.out.println(tree.label);
        for (int i = 0; i < tree.children.size(); i++) {
            boolean isLast = (i == tree.children.size() - 1);
            tree.children.get(i).print("", isLast);
        }
        return tree;
    }
}