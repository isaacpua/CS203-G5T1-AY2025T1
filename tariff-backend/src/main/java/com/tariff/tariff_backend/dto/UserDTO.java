package com.tariff.tariff_backend.dto;
import lombok.Data;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;

@Data
@AllArgsConstructor
public class UserDTO {
    @NotNull
    private String username;
    @NotNull
    private String password;
}
