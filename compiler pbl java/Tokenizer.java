import java.util.*;
// import "C://Users/acer/OneDrive\\Desktop\\Compiler Design Project\\tokenizer\\Parser.java";
class Token {
    String type;
    String value;

    Token(String type, String value) {
        this.type = type;
        this.value = value;
    }

    @Override
    public String toString() {
        return type + "(" + value + ")";
    }
}
class Lexer {
    private final String input;
    private int pos = 0;
    private static final Set<String> keywords = new HashSet<>(Arrays.asList(
        "abstract","assert","boolean","break","byte","case","catch","char","class","const",
        "continue","default","do","double","else","enum","extends","final","finally","float",
        "for","goto","if","implements","import","instanceof","int","interface","long","native",
        "new","package","private","protected","public","return","short","static","strictfp",
        "super","switch","synchronized","this","throw","throws","transient","try","void",
        "volatile","while"
    ));

    Lexer(String input) {
        this.input = input;
    }

    private char peek() {
        if (pos >= input.length()) return '\0';
        return input.charAt(pos);
    }

    private void advance() {
        pos++;
    }

    public List<Token> tokenize() {
        List<Token> tokens = new ArrayList<>();

        while (pos < input.length()) {
            char current = peek();

            if (Character.isWhitespace(current)) {
                advance();
                continue;
            }

            if (Character.isLetter(current)) {
                StringBuilder sb = new StringBuilder();
                while (Character.isLetter(peek()) || Character.isDigit(peek())) {
                    sb.append(peek());
                    advance();
                }
                String word = sb.toString();
                if (keywords.contains(word)) {
                    tokens.add(new Token("KEYWORD", word));
                } else {
                    tokens.add(new Token("IDENTIFIER", word));
                }
                continue;
            }

            if (Character.isDigit(current)) {
                StringBuilder sb = new StringBuilder();
                while (Character.isDigit(peek())) {
                    sb.append(peek());
                    advance();
                }
                tokens.add(new Token("NUMBER", sb.toString()));
                continue;
            }

            if (current == '+' || current == '-' || current == '*' || current == '/' ||
                current == '=' || current == '<' || current == '>' || current == '!') {
                char lookahead = (pos + 1 < input.length()) ? input.charAt(pos + 1) : '\0';
                if ((current == '=' && lookahead == '=') || (current == '<' && lookahead == '=') ||
                    (current == '>' && lookahead == '=') || (current == '!' && lookahead == '=')) {
                    tokens.add(new Token("OPERATOR", "" + current + lookahead));
                    pos += 2;
                } else {
                    tokens.add(new Token("OPERATOR", "" + current));
                    advance();
                }
                continue;
            }

            if (current == ';' || current == '(' || current == ')' || current == '{' || current == '}') {
                tokens.add(new Token("DELIMITER", "" + current));
                advance();
                continue;
            }

            throw new RuntimeException("Unexpected character: " + current);
        }

        return tokens;
    }
}

public class Tokenizer {
    public static void main(String[] args) {
        try (Scanner sc = new Scanner(System.in)) {
            System.out.println("Enter code:");
            String code = sc.nextLine();

            Lexer lexer = new Lexer(code);
            List<Token> tokens = lexer.tokenize();

            System.out.println("\nTokens:");
            for (Token t : tokens) {
                System.out.println(t);
            }

            // Parser parser = new Parser(tokens);
            // parser.parse();

            Syntax syntax = new Syntax(tokens);
            syntax.parse();

            Semantic semantic = new Semantic(tokens);
            semantic.analyse();  
        
            IRGenerator ir = new IRGenerator(tokens, semantic.getSymbolTable());
            ir.generate();
        }
    }
}
