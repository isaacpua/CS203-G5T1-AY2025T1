package com.tariff.tariff_backend.dto;
import lombok.Data;
import lombok.AllArgsConstructor;

@Data
@AllArgsConstructor
public class UserDTO {
    private String username;
    private String password;
}
