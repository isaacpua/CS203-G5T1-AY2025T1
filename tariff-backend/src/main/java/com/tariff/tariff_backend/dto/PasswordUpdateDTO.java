package com.tariff.tariff_backend.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class PasswordUpdateDTO {

    @NotBlank(message = "Password cannot be blank")
    @Size(min = 1, message = "Password must be at least 1 character")
    private String password;
}
