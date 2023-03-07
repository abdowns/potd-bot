#include "common.hpp"

#ifndef COMMANDS_HPP
#define COMMANDS_HPP

namespace cmds
{
    void test(dpp::cluster*, std::string message);
}

static std::map<std::string, std::function<void(dpp::cluster*, std::string)>> commands
{
    cmds::test
};

#endif // COMMANDS_HPP