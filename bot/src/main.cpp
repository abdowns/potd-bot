#include "common.hpp"

json load_config(const std::string path)
{
    json config;
    std::ifstream file(path);
    file >> config;

    return config;
}

int main() {
    json config = load_config("../config.json");

    dpp::cluster bot(config["token"]);
    
    bot.on_slashcommand([](const dpp::slashcommand_t& event) {
            if (event.command.get_command_name() == "ping") {
            event.reply("Pong!");
        }
    });
    
    bot.on_ready([&bot](const dpp::ready_t& event) {
        if (dpp::run_once<struct register_bot_commands>()) {
            bot.global_command_create(
                dpp::slashcommand("ping", "Ping pong!", bot.me.id)
            );
        }
    });
    
    bot.start(dpp::st_wait);
}
