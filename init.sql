SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

CREATE SCHEMA IF NOT EXISTS `mydb` DEFAULT CHARACTER SET utf8 ;
USE `mydb` ;

-- Set global timezone to UTC +8
SET GLOBAL time_zone = '+08:00';

-- Set session timezone to UTC +8
SET time_zone = '+08:00';

-- USER TABLE
CREATE TABLE IF NOT EXISTS `mydb`.`user` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(45) NOT NULL,
  `password` VARCHAR(255) NOT NULL,
  `email` VARCHAR(255) NOT NULL,
  `role` VARCHAR(45) NOT NULL,
  `profile_picture` VARCHAR(255) NULL,
  `locked_until` DATETIME NULL,
  `otp_secret` VARCHAR(32) NULL,
  `otp_enabled` BOOLEAN NOT NULL DEFAULT FALSE,
  `current_session_token` VARCHAR(64) NULL,
  `email_verified` BOOLEAN NOT NULL DEFAULT FALSE,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `id_UNIQUE` (`id` ASC) VISIBLE,
  UNIQUE INDEX `email_UNIQUE` (`email` ASC) VISIBLE
) ENGINE = InnoDB;


-- USER FAILED LOGIN TABLE
CREATE TABLE IF NOT EXISTS `mydb`.`user_failed_login` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `user_id` INT NOT NULL,
    `failed_at` DATETIME NOT NULL,
    PRIMARY KEY (`id`),
    INDEX `idx_user_failed_login_user_id` (`user_id`),
    CONSTRAINT `fk_user_failed_login_user`
        FOREIGN KEY (`user_id`)
        REFERENCES `mydb`.`user` (`id`)
        ON DELETE CASCADE
        ON UPDATE NO ACTION
) ENGINE = InnoDB;

-- USER RESET PASSWORD REQUEST TABLE
CREATE TABLE IF NOT EXISTS `mydb`.`reset_password` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `token_hash` CHAR(64) NOT NULL,
  `expires_at` DATETIME NOT NULL,
  `used` BOOLEAN NOT NULL DEFAULT FALSE,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `token_hash_UNIQUE` (`token_hash` ASC) VISIBLE,
  INDEX `idx_reset_password_user_id` (`user_id` ASC) VISIBLE,
  CONSTRAINT `fk_reset_password_user`
    FOREIGN KEY (`user_id`)
    REFERENCES `mydb`.`user` (`id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION
) ENGINE = InnoDB;


-- SPORTS ACTIVITY
CREATE TABLE IF NOT EXISTS `mydb`.`sports_activity` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `activity_name` VARCHAR(255) NOT NULL,
  `activity_type` VARCHAR(255) NOT NULL,
  `skills_req` VARCHAR(255) NOT NULL,
  `date` DATETIME NOT NULL,
  `location` VARCHAR(255) NOT NULL,
  `max_pax` INT NOT NULL,
  `user_id_list_join` VARCHAR(255) NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_user_id_idx` (`user_id` ASC) VISIBLE,
  CONSTRAINT `fk_user_id`
    FOREIGN KEY (`user_id`)
    REFERENCES `mydb`.`user` (`id`)
    ON DELETE CASCADE  
    ON UPDATE NO ACTION
) ENGINE = InnoDB;


-- FEED TABLE
CREATE TABLE IF NOT EXISTS `mydb`.`feed` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `image_path` VARCHAR(255) NULL,  
  `caption` VARCHAR(255) NULL,
  `like_user_ids` TEXT NULL,
  PRIMARY KEY (`id`),
  INDEX `idx_feed_user_id` (`user_id`),
  CONSTRAINT `fk_feed_user`
    FOREIGN KEY (`user_id`)
    REFERENCES `mydb`.`user` (`id`)
    ON DELETE CASCADE  
    ON UPDATE NO ACTION
) ENGINE = InnoDB;

-- COMMENTS TABLE
CREATE TABLE IF NOT EXISTS `mydb`.`comments` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `feed_id` INT NOT NULL,
  `user_id` INT NOT NULL,
  `comments` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `idx_comments_user_id` (`user_id`),
  INDEX `idx_comments_feed_id` (`feed_id`),
  CONSTRAINT `fk_comments_feed`
    FOREIGN KEY (`feed_id`)
    REFERENCES `mydb`.`feed` (`id`)
    ON DELETE CASCADE  
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_comments_user`
    FOREIGN KEY (`user_id`)
    REFERENCES `mydb`.`user` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
) ENGINE = InnoDB;

SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
