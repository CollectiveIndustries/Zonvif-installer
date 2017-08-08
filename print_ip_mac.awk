    BEGIN { ORS = ""; print " [ "}
    /Network/ {next}
    { printf "%s{\"ip\": \"%s\", \"mac\": \"%s\", \"vendor\": \"%s\", \"onvif\": \"unknown\", \"clock\": \"NTP\", \"dhcp\": \"False\", \"timezone\": \"GMT-07:00\", \"NewIP\": \"0.0.0.0\"}",
          separator, $1, $2, $3
      separator = ", "
    }
    END { print " ] " }

