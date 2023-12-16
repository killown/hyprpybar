#include "integration-test-common.h"

static GtkWindow* window;

static void set_anchors(GtkWindow* window, gboolean top, gboolean bottom, gboolean left, gboolean right)
{
    gtk_layer_set_anchor(window, GTK_LAYER_SHELL_EDGE_TOP, top);
    gtk_layer_set_anchor(window, GTK_LAYER_SHELL_EDGE_BOTTOM, bottom);
    gtk_layer_set_anchor(window, GTK_LAYER_SHELL_EDGE_LEFT, left);
    gtk_layer_set_anchor(window, GTK_LAYER_SHELL_EDGE_RIGHT, right);
}

static void callback_0()
{
    EXPECT_MESSAGE(zwlr_layer_surface_v1 .set_anchor 0);
    EXPECT_MESSAGE(wl_surface .commit);

    window = create_default_window();
    gtk_layer_init_for_window(window);
    gtk_window_present(window);

    set_anchors(window, FALSE, FALSE, FALSE, FALSE);
}

static void callback_1()
{
    EXPECT_MESSAGE(zwlr_layer_surface_v1 .set_anchor 3);
    EXPECT_MESSAGE(wl_surface .commit);
    set_anchors(window, TRUE, TRUE, FALSE, FALSE);
}

static void callback_2()
{
    EXPECT_MESSAGE(zwlr_layer_surface_v1 .set_anchor 13);
    EXPECT_MESSAGE(wl_surface .commit);
    set_anchors(window, TRUE, FALSE, TRUE, TRUE);
}

static void callback_3()
{
    EXPECT_MESSAGE(zwlr_layer_surface_v1 .set_anchor 15);
    EXPECT_MESSAGE(wl_surface .commit);
    set_anchors(window, TRUE, TRUE, TRUE, TRUE);
}

static void callback_4()
{
    EXPECT_MESSAGE(zwlr_layer_surface_v1 .set_anchor 0);
    EXPECT_MESSAGE(wl_surface .commit);
    set_anchors(window, FALSE, FALSE, FALSE, FALSE);
}

TEST_CALLBACKS(
    callback_0,
    callback_1,
    callback_2,
    callback_3,
    callback_4,
)
