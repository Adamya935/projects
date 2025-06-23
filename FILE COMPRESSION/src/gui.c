#include <gtk/gtk.h>
#include "huffman.h"

static GtkWidget *window;
static GtkWidget *input_entry;
static GtkWidget *output_entry;

static void show_message(const char *message) {
    GtkWidget *dialog = gtk_message_dialog_new(GTK_WINDOW(window),
        GTK_DIALOG_MODAL, GTK_MESSAGE_INFO, GTK_BUTTONS_OK, "%s", message);
    gtk_dialog_run(GTK_DIALOG(dialog));
    gtk_widget_destroy(dialog);
}

static void on_compress_clicked(GtkWidget *widget, gpointer data) {
    const char *input_file = gtk_entry_get_text(GTK_ENTRY(input_entry));
    const char *output_file = gtk_entry_get_text(GTK_ENTRY(output_entry));

    if (!input_file || *input_file == '\0' || !output_file || *output_file == '\0') {
        show_message("Please enter both input and output file paths.");
        return;
    }

    int res = compress_file(input_file, output_file);
    if (res == 0) show_message("Compression successful!");
    else if (res == 2) show_message("Compression skipped: output larger than input.");
    else show_message("Compression failed!");
}

static void on_decompress_clicked(GtkWidget *widget, gpointer data) {
    const char *input_file = gtk_entry_get_text(GTK_ENTRY(input_entry));
    const char *output_file = gtk_entry_get_text(GTK_ENTRY(output_entry));

    if (!input_file || *input_file == '\0' || !output_file || *output_file == '\0') {
        show_message("Please enter both input and output file paths.");
        return;
    }

    int res = decompress_file(input_file, output_file);
    if (res == 0) show_message("Decompression successful!");
    else show_message("Decompression failed!");
}

int main(int argc, char *argv[]) {
    gtk_init(&argc, &argv);

    window = gtk_window_new(GTK_WINDOW_TOPLEVEL);
    gtk_window_set_title(GTK_WINDOW(window), "Huffman Compressor");
    gtk_window_set_default_size(GTK_WINDOW(window), 450, 180);
    g_signal_connect(window, "destroy", G_CALLBACK(gtk_main_quit), NULL);

    GtkWidget *vbox = gtk_box_new(GTK_ORIENTATION_VERTICAL, 10);
    gtk_container_add(GTK_CONTAINER(window), vbox);

    GtkWidget *input_label = gtk_label_new("Input File Path:");
    gtk_box_pack_start(GTK_BOX(vbox), input_label, FALSE, FALSE, 0);

    input_entry = gtk_entry_new();
    gtk_entry_set_placeholder_text(GTK_ENTRY(input_entry), "Enter input file path here");
    gtk_box_pack_start(GTK_BOX(vbox), input_entry, FALSE, FALSE, 0);

    GtkWidget *output_label = gtk_label_new("Output File Path:");
    gtk_box_pack_start(GTK_BOX(vbox), output_label, FALSE, FALSE, 0);

    output_entry = gtk_entry_new();
    gtk_entry_set_placeholder_text(GTK_ENTRY(output_entry), "Enter output file path here");
    gtk_box_pack_start(GTK_BOX(vbox), output_entry, FALSE, FALSE, 0);

    GtkWidget *hbox = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 10);
    gtk_box_pack_start(GTK_BOX(vbox), hbox, FALSE, FALSE, 10);

    GtkWidget *compress_btn = gtk_button_new_with_label("Compress");
    GtkWidget *decompress_btn = gtk_button_new_with_label("Decompress");

    gtk_box_pack_start(GTK_BOX(hbox), compress_btn, TRUE, TRUE, 0);
    gtk_box_pack_start(GTK_BOX(hbox), decompress_btn, TRUE, TRUE, 0);

    g_signal_connect(compress_btn, "clicked", G_CALLBACK(on_compress_clicked), NULL);
    g_signal_connect(decompress_btn, "clicked", G_CALLBACK(on_decompress_clicked), NULL);

    gtk_widget_show_all(window);
    gtk_main();

    return 0;
}
